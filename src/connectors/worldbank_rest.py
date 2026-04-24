"""World Bank debarment REST connector.

Pagination: offset-based (?offset=N&limit=M).
Checkpoint position: integer offset of the last fetched page.

NOTE: Response shape is inferred from public WB debarment API patterns.
Verify field names against a live response before production use.
"""
from collections.abc import Iterator

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from src.config import AppConfig
from src.connectors.base_connector import BaseConnector, FetchPage
from src.errors import ConnectorError
from src.logger import get_logger

log = get_logger(__name__)


class WorldBankConnector(BaseConnector):
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    @property
    def source_system(self) -> str:
        return "worldbank"

    def fetch_pages(self, start_position: str | int | None) -> Iterator[FetchPage]:
        if start_position is not None:
            log.info("WorldBank API does not support pagination. Ignoring start_position=%s", start_position)

        with httpx.Client(timeout=self._config.worldbank_timeout_seconds) as client:
            try:
                body = self._get(client)
            except httpx.HTTPStatusError as exc:
                raise ConnectorError(f"WorldBank HTTP {exc.response.status_code}") from exc
            except httpx.RequestError as exc:
                raise ConnectorError(f"WorldBank request failed: {exc}") from exc

            try:
                all_records = body["response"]["ZPROCSUPP"]
            except (KeyError, TypeError) as exc:
                raise ConnectorError(f"Unexpected World Bank API schema: {exc}") from exc

            batch_size = self._config.batch_size
            if not all_records:
                yield FetchPage(records=[], position=1, is_last=True)
                return

            for i in range(0, len(all_records), batch_size):
                chunk = all_records[i : i + batch_size]
                is_last = (i + batch_size) >= len(all_records)
                
                yield FetchPage(
                    records=chunk,
                    position=(i // batch_size) + 1,
                    is_last=is_last,
                )

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True,
    )
    def _get(self, client: httpx.Client) -> dict:
        headers = {
            "apikey": self._config.worldbank_api_key,
            "Origin": "https://www.worldbank.org",
            "Referer": "https://www.worldbank.org/",
            "Accept": "application/json",
        }
        response = client.get(
            self._config.worldbank_api_url,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()
