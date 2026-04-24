from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Checkpoint:
    """Persisted position for incremental runs.

    position:
      - int  → page number  (inaproc)
      - int  → REST offset   (worldbank)
      - None → not started
    """

    strategy: str  # "page" | "offset"
    position: str | int | None
    last_run_at: str | None  # ISO 8601


def empty_checkpoint(strategy: str) -> Checkpoint:
    return Checkpoint(strategy=strategy, position=None, last_run_at=None)


def checkpoint_now(strategy: str, position: str | int) -> Checkpoint:
    return Checkpoint(
        strategy=strategy,
        position=position,
        last_run_at=datetime.now(timezone.utc).isoformat(),
    )
