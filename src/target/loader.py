"""Loader — sends validated records in batches to target API.

Partial batch failure behaviour:
  - Records in "errors" from target API response → dead-letter, not counted as loaded.
  - Successfully inserted records → loaded count incremented.
  - Checkpoint is NOT updated here; the orchestrator updates it after this returns.
  - If the entire POST fails (network/5xx after retries), raises ConnectorError
    so the orchestrator can skip the checkpoint update for this page.
"""
from dataclasses import dataclass

from src.errors import ConnectorError, TargetAPIError
from src.logger import get_logger
from src.report import dead_letter as dl
from src.report.run_report import RunReport
from src.target.payload_builder import build_payload, parse_response
from src.target.target_api_client import TargetAPIClient
from src.models import CanonicalRecord

log = get_logger(__name__)


@dataclass
class BatchResult:
    loaded: int
    failed: int


def load_batch(
    records: list[CanonicalRecord],
    client: TargetAPIClient,
    dataset_uid: str,
    source: str,
    run_id: str,
    output_dir: str,
    dry_run: bool,
    report: RunReport,
) -> BatchResult:
    """Send one batch to target API. Updates report counters in-place.

    Raises:
        ConnectorError: On total batch failure (network/5xx after retries).
    """
    if dry_run:
        log.info("[dry-run] Would send %d records to dataset %s", len(records), dataset_uid)
        
        import json
        import os
        os.makedirs(output_dir, exist_ok=True)
        dump_path = os.path.join(output_dir, f"dry_run_{source}_{run_id}.json")
        with open(dump_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(build_payload(records), ensure_ascii=False) + "\n")
            
        log.info("[dry-run] Payload saved to %s", dump_path)

        report.loaded += len(records)
        return BatchResult(loaded=len(records), failed=0)

    payload = build_payload(records)
    try:
        body = client.post_batch(dataset_uid, payload)
    except TargetAPIError as exc:
        # Non-retryable 4xx — dead-letter entire batch
        for record in records:
            dl.append(record.model_dump(), str(exc), "loader", source, run_id, output_dir)
        report.failed += len(records)
        log.error("Batch rejected by target API (4xx): %s", exc)
        return BatchResult(loaded=0, failed=len(records))
    except Exception as exc:
        raise ConnectorError(f"Batch POST failed: {exc}") from exc

    inserted, errors = parse_response(body)
    failed_indices: set[int] = {e["index"] for e in errors}

    for i, record in enumerate(records):
        if i in failed_indices:
            reason = next((e["message"] for e in errors if e["index"] == i), "unknown")
            dl.append(record.model_dump(), reason, "loader", source, run_id, output_dir)
            report.failed += 1
        else:
            report.loaded += 1

    return BatchResult(loaded=inserted, failed=len(failed_indices))
