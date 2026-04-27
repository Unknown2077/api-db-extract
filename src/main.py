"""Entry point for simple ETL pipeline."""
from src.config import load_config
from src.connectors import inaproc, worldbank
from src.errors import ConfigError
from src.logger import get_logger
from src.mappers.inaproc_mapper import map_inaproc
from src.mappers.worldbank_mapper import map_worldbank
from src.target.payload_builder import build_payload
from src.target.target_api_client import TargetAPIClient

log = get_logger(__name__)


def main() -> None:
    try:
        config = load_config()
    except ConfigError as exc:
        log.error("Configuration error: %s", exc)
        return

    # Inaproc
    try:
        log.info("Starting Inaproc extraction...")
        raw_inaproc = inaproc.fetch_all(config)
        mapped_inaproc = []
        for raw in raw_inaproc:
            try:
                mapped_inaproc.append(map_inaproc(raw))
            except Exception as e:
                log.warning("Skipping Inaproc record mapping error: %s", e)

        if mapped_inaproc:
            log.info("Inserting %d Inaproc records...", len(mapped_inaproc))
            with TargetAPIClient(config) as client:
                payload = build_payload(mapped_inaproc)
                client.post_batch(config.target_api_dataset_uid_inaproc, payload)
            log.info("Inaproc insertion complete.")
    except Exception as e:
        log.error("Inaproc pipeline failed: %s", e)
    # === WORLD BANK (COMMENTED OUT FOR TESTING) ===
    # try:
    #     log.info("Starting World Bank extraction...")
    #     raw_worldbank = worldbank.fetch_all(config)
    #     mapped_worldbank = []
    #     for raw in raw_worldbank:
    #         try:
    #             mapped_worldbank.append(map_worldbank(raw))
    #         except Exception as e:
    #             log.warning("Skipping World Bank record mapping error: %s", e)
    # 
    #     if mapped_worldbank:
    #         log.info("Inserting %d World Bank records...", len(mapped_worldbank))
    #         with TargetAPIClient(config) as client:
    #             payload = build_payload(mapped_worldbank)
    #             client.post_batch(config.target_api_dataset_uid_worldbank, payload)
    #         log.info("World Bank insertion complete.")
    # except Exception as e:
    #     log.error("World Bank pipeline failed: %s", e)
    log.info("Pipeline complete.")


if __name__ == "__main__":
    main()
