"""Entry point for simple ETL pipeline."""
from typing import Any


from src.config import load_config
from src.connectors import inaproc, worldbank
from src.errors import ConfigError
from src.logger import get_logger
from src.mappers.inaproc_mapper import map_inaproc, map_inaproc_blacklist_registry
from src.mappers.worldbank_mapper import map_worldbank, map_worldbank_debarment
from src.models import InaprocBlacklistRegistry, WorldBankDebarment
from src.target.payload_builder import build_payload
from src.target.target_api_client import TargetAPIClient

log = get_logger(__name__)


def _dedupe_inaproc_keep_latest(
    records: list[InaprocBlacklistRegistry],
) -> list[InaprocBlacklistRegistry]:
    by_id: dict[str, InaprocBlacklistRegistry] = {}
    for record in records:
        by_id[record.id] = record
    return list(by_id.values())


def main() -> None:
    try:
        config = load_config()
    except ConfigError as exc:
        log.error("Configuration error: %s", exc)
        return

    try:
        log.info("Starting Inaproc extraction...")
        raw_inaproc = inaproc.fetch_all(config)
        mapped_inaproc: list[InaprocBlacklistRegistry] = []
        for index, raw in enumerate(raw_inaproc):
            try:
                mapped = map_inaproc_blacklist_registry(raw)
                mapped_inaproc.append(mapped)
            except Exception as e:
                log.warning("Skipping Inaproc record mapping error: %s", e)   

        if mapped_inaproc:
            before_count = len(mapped_inaproc)
            mapped_inaproc = _dedupe_inaproc_keep_latest(mapped_inaproc)
            after_count = len(mapped_inaproc)
            removed_duplicates = before_count - after_count
            log.info(
                "Inaproc dedupe by id (keep-latest): before=%d after=%d removed_duplicates=%d",
                before_count,
                after_count,
                removed_duplicates,
            )

        if mapped_inaproc:
            log.info("Inserting %d Inaproc records...", len(mapped_inaproc))
            with TargetAPIClient(config) as client:
                payload = build_payload(mapped_inaproc)
                client.post_batch(config.target_api_dataset_uid_inaproc, payload)
            log.info("Inaproc insertion complete.")
    except Exception as e:
        log.error("Inaproc pipeline failed: %s", e)

    try:
        log.info("Starting World Bank extraction...")
        raw_worldbank = worldbank.fetch_all(config)
        mapped_worldbank: list[WorldBankDebarment] = []
        for raw in raw_worldbank:
            try:
                mapped = map_worldbank_debarment(raw)
                mapped_worldbank.append(mapped)
            except Exception as e:
                log.warning("Skipping World Bank record mapping error: %s", e)
    
        if mapped_worldbank:
            log.info("Inserting %d World Bank records...", len(mapped_worldbank))
            with TargetAPIClient(config) as client:
                payload = build_payload(mapped_worldbank)
                client.post_batch(config.target_api_dataset_uid_worldbank, payload)
            log.info("World Bank insertion complete.")
    except Exception as e:
        log.error("World Bank pipeline failed: %s", e)
    log.info("Pipeline complete.")


if __name__ == "__main__":
    main()
