"""Target API HTTP client — handles auth, retry, and error classification."""
import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from src.config import AppConfig
from src.errors import TargetAPIError
from src.logger import get_logger

log = get_logger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class TargetAPIClient:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client = httpx.Client(timeout=config.target_api_timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TargetAPIClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def post_batch(self, dataset_uid: str, payload: dict) -> dict:
        """POST payload to target dataset. Returns parsed response body.

        Retries on network errors, 429, and 5xx.
        Raises TargetAPIError on non-retryable 4xx.
        """
        url = (
            self._config.target_api_base_url.rstrip("/")
            + self._config.target_api_insert_path.format(
                account_uid=self._config.target_api_account_uid,
                dataset_uid=dataset_uid,
            )
        )
        return self._post_with_retry(url, payload)

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        reraise=True,
    )
    def _post_with_retry(self, url: str, payload: dict) -> dict:
        response = self._client.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {self._config.target_api_token}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code in _RETRYABLE_STATUS:
            log.warning("Retryable status %s from target API", response.status_code)
            response.raise_for_status()  # triggers tenacity retry via HTTPStatusError

        if response.is_client_error:
            raise TargetAPIError(response.status_code, response.text[:500])

        return response.json()
