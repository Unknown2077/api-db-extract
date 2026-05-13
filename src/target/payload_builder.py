"""Target API payload builder.

Finalised payload contract:
  POST {base_url}/api/v1/accounts/{account_uid}/datasets/{dataset_uid}/data
  Content-Type: application/json
  Authorization: Bearer {token}

  Request body:
    { "data": [ <CanonicalRecord as dict>, ... ] }

  Response body (success 2xx):
    { "inserted": <int>, "errors": [ {"index": <int>, "message": "<str>"} ] }

  - "inserted" = count of records accepted
  - "errors"   = per-record failures (non-retryable payload issues)
  - 4xx (excl. 429) = non-retryable, raises TargetAPIError
  - 429 / 5xx       = retryable via tenacity
"""
from typing import Any

from pydantic import BaseModel
from src.models import CanonicalRecord



def build_payload(records: list[BaseModel]) -> dict:
    return {"rows": [r.model_dump(mode="json") for r in records]}


def parse_response(response_body: dict) -> tuple[int, list[dict]]:
    """Return (inserted_count, error_list) from target API response body."""
    inserted: int = response_body.get("inserted", 0)
    errors: list[dict] = response_body.get("errors", [])
    return inserted, errors
