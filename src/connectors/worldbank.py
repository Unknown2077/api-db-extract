"""World Bank debarment REST connector — fetch all sanctioned firms."""
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from src.config import AppConfig
from src.errors import ConnectorError
from src.logger import get_logger

log = get_logger(__name__)


def fetch_all(config: AppConfig) -> list[dict]:
    """Fetch all debarred firms/individuals from World Bank API."""
    with httpx.Client(timeout=config.worldbank_timeout_seconds) as client:
        try:
            body = _get(client, config)
        except httpx.HTTPStatusError as exc:
            raise ConnectorError(f"WorldBank HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise ConnectorError(f"WorldBank request failed: {exc}") from exc

    try:
        records: list[dict] = body["response"]["ZPROCSUPP"]
    except (KeyError, TypeError) as exc:
        raise ConnectorError(f"Unexpected World Bank API schema: {exc}") from exc

    log.info("WorldBank fetch complete: %d records total", len(records))
    return records


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    reraise=True,
)
def _get(client: httpx.Client, config: AppConfig) -> dict:
    headers = {
        "apikey": config.worldbank_api_key,
        "Origin": "https://www.worldbank.org",
        "Referer": "https://www.worldbank.org/",
        "Accept": "application/json",
    }
    response = client.get(config.worldbank_api_url, headers=headers)
    response.raise_for_status()
    return response.json()
