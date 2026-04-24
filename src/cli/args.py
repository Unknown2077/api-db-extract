"""CLI argument parser using Typer."""
from typing import Annotated

import typer

app = typer.Typer(name="api-db-extract", add_completion=False)

SourceArg = Annotated[
    str,
    typer.Option(
        "--source",
        help="Data source to extract: inaproc | worldbank | all",
        show_default=True,
    ),
]

ModeArg = Annotated[
    str,
    typer.Option(
        "--mode",
        help="Run mode: incremental (resume from checkpoint) | full-refresh (ignore checkpoint)",
        show_default=True,
    ),
]

DryRunArg = Annotated[
    bool,
    typer.Option("--dry-run/--no-dry-run", help="Skip sending data to target API"),
]
