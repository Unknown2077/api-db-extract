"""Dead-letter writer — one JSONL file per source per run."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def append(
    record: dict,
    reason: str,
    stage: str,
    source: str,
    run_id: str,
    output_dir: str,
) -> None:
    """Append one failed record to the dead-letter JSONL file.

    Args:
        record: Raw or canonical dict of the failed record.
        reason: Human-readable failure description.
        stage:  "mapper" | "validator" | "loader"
        source: "inaproc" | "worldbank"
        run_id: Current run identifier (used in filename).
        output_dir: Directory where the file is written.
    """
    os.makedirs(output_dir, exist_ok=True)
    path = Path(output_dir) / f"dead_letter_{source}_{run_id}.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "reason": reason,
        "record": record,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
