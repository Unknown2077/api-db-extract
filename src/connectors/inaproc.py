"""Inaproc GraphQL connector — fetch all blacklist records."""
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from src.config import AppConfig
from src.errors import ConnectorError
from src.logger import get_logger

log = get_logger(__name__)

_QUERY = """
query GetBlacklists($input: BlacklistsInput) {
  blacklists(input: $input) {
    blacklists {
      id
      skNumber
      skNumberStatusBased
      status
      startDate
      expiredDate
      publishDate
      publishDurationInMinutes
      status
      statusUpdatedAt
      tender {
        id
        name
        packageId
        pagu
        hps
        budgetYear
        category
      }
      provider {
        id
        name
        npwp
        address
        additionalAddress
      }
      document {
        id
        name
        blacklistId
        additionalInfo
      }
      correspondence {
        lpse {
          id
          name
        }
        kldi {
          name
          id
        }
        satker {
          id
          name
        }
      }
      violation {
        id
        name
        description
        month
        year
      }
    }
    pagination {
      pageNumber
      totalPage
      totalData
    }
  }
}
"""

_HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://daftar-hitam.inaproc.id",
    "Referer": "https://daftar-hitam.inaproc.id/",
}


def fetch_all(config: AppConfig) -> list[dict]:
    """Fetch all blacklist records from Inaproc GraphQL API."""
    all_records: list[dict] = []
    page_number = 1
    per_page = 1000

    with httpx.Client(timeout=config.inaproc_timeout_seconds) as client:
        while True:
            try:
                data = _post(client, config.inaproc_graphql_url, page_number, per_page)
            except httpx.HTTPStatusError as exc:
                raise ConnectorError(f"Inaproc HTTP {exc.response.status_code}") from exc
            except httpx.RequestError as exc:
                raise ConnectorError(f"Inaproc request failed: {exc}") from exc

            result = data.get("blacklists", {})
            records: list[dict] = result.get("blacklists", [])
            pagination = result.get("pagination", {})

            total_page: int = pagination.get("totalPage", 1)
            total_data: int = pagination.get("totalData", 0)

            log.info(
                "Inaproc page %d/%d — %d records (total %d)",
                page_number, total_page, len(records), total_data,
            )

            all_records.extend(records)

            if page_number >= total_page or len(records) == 0:
                break
            page_number += 1

    log.info("Inaproc fetch complete: %d records total", len(all_records))
    return all_records


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    reraise=True,
)
def _post(client: httpx.Client, url: str, page_number: int, per_page: int) -> dict:
    response = client.post(
        url,
        json={
            "query": _QUERY,
            "variables": {
                "input": {
                    "filter": {},
                    "pagination": {
                        "pageNumber": page_number,
                        "perPage": per_page,
                    },
                },
            },
            "operationName": "GetBlacklists",
        },
        headers=_HEADERS,
    )
    response.raise_for_status()
    body = response.json()
    if "errors" in body:
        raise ConnectorError(f"GraphQL errors: {body['errors']}")
    return body.get("data", {})
