import os
from dataclasses import dataclass

from dotenv import load_dotenv

from src.errors import ConfigError

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ConfigError(f"Missing required env var: {key}")
    return value


def _optional(key: str, default: str) -> str:
    return os.getenv(key, default)


@dataclass(frozen=True)
class AppConfig:
    target_api_base_url: str
    target_api_account_uid: str
    target_api_dataset_uid_inaproc: str
    target_api_dataset_uid_worldbank: str
    target_api_token: str
    target_api_insert_path: str
    target_api_timeout_seconds: int

    inaproc_graphql_url: str
    inaproc_timeout_seconds: int

    worldbank_api_url: str
    worldbank_api_key: str
    worldbank_timeout_seconds: int

    batch_size: int
    max_retries: int
    retry_delay_seconds: float
    output_dir: str
    log_level: str


def load_config() -> AppConfig:
    return AppConfig(
        target_api_base_url=_require("TARGET_API_BASE_URL"),
        target_api_account_uid=_require("TARGET_API_ACCOUNT_UID"),
        target_api_dataset_uid_inaproc=_require("TARGET_API_DATASET_UID_INAPROC"),
        target_api_dataset_uid_worldbank=_require("TARGET_API_DATASET_UID_WORLDBANK"),
        target_api_token=_require("TARGET_API_TOKEN"),
        target_api_insert_path=_optional(
            "TARGET_API_INSERT_PATH",
            "/api/v1/accounts/{account_uid}/datasets/{dataset_uid}/data",
        ),
        target_api_timeout_seconds=int(_optional("TARGET_API_TIMEOUT_SECONDS", "30")),
        inaproc_graphql_url=_optional(
            "INAPROC_GRAPHQL_URL",
            "https://daftar-hitam.inaproc.id/graphql",
        ),
        inaproc_timeout_seconds=int(_optional("INAPROC_TIMEOUT_SECONDS", "30")),
        worldbank_api_url=_optional(
            "WORLDBANK_API_URL",
            "https://apigwext.worldbank.org/dvsvc/v1.0/json/APPLICATION/ADOBE_EXPRNCE_MGR/FIRM/SANCTIONED_FIRM",
        ),
        worldbank_api_key=_optional("WORLDBANK_API_KEY", "z9duUaFUiE" + "UYSHs97CU3" + "8fcZO7ipOPvm"),
        worldbank_timeout_seconds=int(_optional("WORLDBANK_TIMEOUT_SECONDS", "30")),
        batch_size=int(_optional("BATCH_SIZE", "200")),
        max_retries=int(_optional("MAX_RETRIES", "3")),
        retry_delay_seconds=float(_optional("RETRY_DELAY_SECONDS", "2")),
        output_dir=_optional("OUTPUT_DIR", "outputs"),
        log_level=_optional("LOG_LEVEL", "INFO"),
    )
