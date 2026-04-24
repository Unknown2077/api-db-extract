"""Run report — accumulated counters, saved as JSON at end of run."""
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RunReport:
    source: str
    mode: str
    dry_run: bool
    run_id: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    finished_at: str | None = None

    fetched: int = 0
    mapped: int = 0
    valid: int = 0
    invalid: int = 0
    deduped: int = 0
    loaded: int = 0
    failed: int = 0

    def finish(self) -> None:
        self.finished_at = datetime.now(timezone.utc).isoformat()

    def save(self, output_dir: str) -> None:
        os.makedirs(output_dir, exist_ok=True)
        path = Path(output_dir) / f"report_{self.source}_{self.run_id}.json"
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False))
