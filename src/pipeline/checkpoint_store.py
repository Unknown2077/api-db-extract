"""Checkpoint persistence — load/save per source to outputs/.

Checkpoint file: {output_dir}/checkpoint_{source}.json

Strategy:
  inaproc   → page-based   (int pageNumber)
  worldbank → offset-based  (int page offset)

Checkpoint is ONLY saved after a batch successfully loads to target API.
"""
import json
import os
from pathlib import Path

from src.pipeline.checkpoint import Checkpoint, empty_checkpoint


def _path(output_dir: str, source: str) -> Path:
    return Path(output_dir) / f"checkpoint_{source}.json"


def load(source: str, output_dir: str) -> Checkpoint:
    p = _path(output_dir, source)
    if not p.exists():
        strategy = "page" if source == "inaproc" else "offset"
        return empty_checkpoint(strategy)
    data = json.loads(p.read_text())
    return Checkpoint(
        strategy=data["strategy"],
        position=data.get("position"),
        last_run_at=data.get("last_run_at"),
    )


def save(checkpoint: Checkpoint, source: str, output_dir: str) -> None:
    p = _path(output_dir, source)
    os.makedirs(p.parent, exist_ok=True)
    p.write_text(
        json.dumps(
            {
                "strategy": checkpoint.strategy,
                "position": checkpoint.position,
                "last_run_at": checkpoint.last_run_at,
            },
            indent=2,
        )
    )
