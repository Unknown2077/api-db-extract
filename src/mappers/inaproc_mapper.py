"""Inaproc raw dict → CanonicalRecord.

Expected raw keys (from real GetBlacklists GraphQL response):
  id, skNumber, startDate, expiredDate, status,
  provider.name, provider.npwp, provider.address,
  violation.name, violation.description,
  tender.name, correspondence.*, document.*

Date fields are normalised to ISO 8601 YYYY-MM-DD.
Raises MapperError on any required field absence or unparseable date.
"""
from src.errors import MapperError
from src.types import CanonicalRecord
from src.utils import parse_date_iso

_SOURCE_URL = "https://daftar-hitam.inaproc.id"


def map_inaproc(raw: dict) -> CanonicalRecord:
    record_id = str(raw.get("id", "")).strip()
    if not record_id:
        raise MapperError("id", "missing or empty")

    provider = raw.get("provider") or {}
    entity_name = str(provider.get("name", "")).strip()
    if not entity_name:
        raise MapperError("provider.name", "missing or empty")

    try:
        effective_date = parse_date_iso(raw.get("startDate"))
    except ValueError as exc:
        raise MapperError("startDate", str(exc)) from exc

    try:
        end_date = parse_date_iso(raw.get("expiredDate"))
    except ValueError as exc:
        raise MapperError("expiredDate", str(exc)) from exc

    violation = raw.get("violation") or {}
    reason = violation.get("name") or violation.get("description") or None

    return CanonicalRecord(
        source_system="inaproc",
        source_url=_SOURCE_URL,
        source_record_id=record_id,
        entity_name=entity_name,
        country="Indonesia",
        reason=reason,
        effective_date=effective_date,
        end_date=end_date,
        reference_id=raw.get("skNumber") or None,
        raw_payload=dict(raw),
    )
