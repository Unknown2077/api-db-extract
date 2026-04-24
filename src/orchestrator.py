"""Orchestrator — wires the full ETL pipeline for one source.

Checkpoint strategy:
  - Checkpoint is loaded before fetch.
  - full-refresh mode ignores the checkpoint start position.
  - Checkpoint is saved ONLY after a batch's load_batch() call succeeds
    (i.e., POST did not raise ConnectorError).
  - Partial batch failures (per-record API errors) still advance the checkpoint
    because the failed records are routed to dead-letter.

Dead-letter responsibility is here, NOT in normalizer.
"""
from datetime import datetime, timezone

from src.config import AppConfig
from src.connectors.base_connector import BaseConnector
from src.connectors.inaproc_graphql import InaprocConnector
from src.connectors.worldbank_rest import WorldBankConnector
from src.errors import ConnectorError, MapperError
from src.logger import get_logger
from src.pipeline import checkpoint_store
from src.pipeline.checkpoint import checkpoint_now
from src.pipeline.deduplicator import deduplicate
from src.pipeline.normalizer import normalize
from src.pipeline.validator import validate
from src.report import dead_letter as dl
from src.report.run_report import RunReport
from src.target.loader import load_batch
from src.target.target_api_client import TargetAPIClient
from src.types import CanonicalRecord

log = get_logger(__name__)


def _make_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


def _dataset_uid(source: str, config: AppConfig) -> str:
    return (
        config.target_api_dataset_uid_inaproc
        if source == "inaproc"
        else config.target_api_dataset_uid_worldbank
    )


def _connector(source: str, config: AppConfig) -> BaseConnector:
    if source == "inaproc":
        return InaprocConnector(config)
    if source == "worldbank":
        return WorldBankConnector(config)
    raise ValueError(f"Unknown source: {source!r}")


def run_source(
    source: str,
    config: AppConfig,
    mode: str,  # "incremental" | "full-refresh"
    dry_run: bool,
) -> RunReport:
    run_id = _make_run_id()
    report = RunReport(source=source, mode=mode, dry_run=dry_run, run_id=run_id)

    checkpoint = checkpoint_store.load(source, config.output_dir)
    start_position = None if mode == "full-refresh" else checkpoint.position

    log.info(
        "Starting %s | source=%s | mode=%s | dry_run=%s | position=%s",
        run_id, source, mode, dry_run, start_position,
    )

    connector = _connector(source, config)
    dataset_uid = _dataset_uid(source, config)

    with TargetAPIClient(config) as client:
        consecutive_failures = 0
        
        for page in connector.fetch_pages(start_position):
            page_valid: list[CanonicalRecord] = []

            for raw in page.records:
                report.fetched += 1
                try:
                    record = normalize(raw, source)
                except (MapperError, KeyError) as exc:
                    dl.append(raw, str(exc), "mapper", source, run_id, config.output_dir)
                    report.invalid += 1
                    continue

                report.mapped += 1
                is_valid, reason = validate(record)
                if not is_valid:
                    dl.append(
                        record.model_dump(), reason or "invalid", "validator",
                        source, run_id, config.output_dir,
                    )
                    report.invalid += 1
                    continue

                report.valid += 1
                page_valid.append(record)

            unique_records, deduped_count = deduplicate(page_valid)
            report.deduped += deduped_count

            if not unique_records:
                log.debug("Page yielded no valid unique records; advancing checkpoint")
                checkpoint_store.save(
                    checkpoint_now(checkpoint.strategy, page.position),
                    source,
                    config.output_dir,
                )
                continue

            try:
                batch_result = load_batch(
                    unique_records, client, dataset_uid,
                    source, run_id, config.output_dir, dry_run, report,
                )
                
                if batch_result.loaded == 0 and batch_result.failed > 0:
                    consecutive_failures += 1
                else:
                    consecutive_failures = 0

                # Checkpoint only after successful load (no ConnectorError raised)
                checkpoint_store.save(
                    checkpoint_now(checkpoint.strategy, page.position),
                    source,
                    config.output_dir,
                )
                
                if consecutive_failures >= 3:
                    log.error("Aborting run: 3 consecutive full batch failures detected.")
                    break
                    
            except ConnectorError as exc:
                log.error(
                    "Page load failed — checkpoint NOT advanced: %s", exc
                )
                # Do not save checkpoint; next run will retry this page
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    log.error("Aborting run: 3 consecutive connector/network errors detected.")
                    break

    report.finish()
    report.save(config.output_dir)
    log.info(
        "Run complete: fetched=%d valid=%d loaded=%d failed=%d",
        report.fetched, report.valid, report.loaded, report.failed,
    )
    return report
