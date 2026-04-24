"""Entry point."""
import typer

from src.cli.args import DryRunArg, ModeArg, SourceArg, app
from src.config import load_config
from src.errors import ConfigError
from src.logger import get_logger
from src.orchestrator import run_source

log = get_logger(__name__)

_VALID_SOURCES = {"inaproc", "worldbank"}
_VALID_MODES = {"incremental", "full-refresh"}


@app.command()
def main(
    source: SourceArg = "all",
    mode: ModeArg = "incremental",
    dry_run: DryRunArg = False,
) -> None:
    if mode not in _VALID_MODES:
        raise typer.BadParameter(f"--mode must be one of: {', '.join(_VALID_MODES)}")

    sources = _VALID_SOURCES if source == "all" else {source}
    if not sources.issubset(_VALID_SOURCES):
        raise typer.BadParameter(f"--source must be one of: all, {', '.join(_VALID_SOURCES)}")

    try:
        config = load_config()
    except ConfigError as exc:
        log.error("Configuration error: %s", exc)
        raise typer.Exit(code=1) from exc

    for src in sorted(sources):
        run_source(src, config, mode, dry_run)


if __name__ == "__main__":
    app()
