"""World Bank raw dict → CanonicalRecord.

Expected raw keys (REST response rows):
  firmName, country, fromDate, toDate, grounds, ineligibilityStatusDate

Date fields are normalised to ISO 8601 YYYY-MM-DD.
Raises MapperError on any required field absence or unparseable date.
"""
from src.errors import MapperError
from src.types import CanonicalRecord
from src.utils import parse_date_iso

_SOURCE_URL = "https://apigwext.worldbank.org"


def map_worldbank(raw: dict) -> CanonicalRecord:
    entity_name = str(raw.get("SUPP_NAME", "")).strip()
    if not entity_name:
        raise MapperError("SUPP_NAME", "missing or empty")

    record_id = str(raw.get("SUPP_ID", "")).strip()
    if not record_id or record_id == "0":
        from_raw = str(raw.get("DEBAR_FROM_DATE", "")).strip()
        record_id = f"{entity_name}|{from_raw}" if from_raw else entity_name

    try:
        effective_date = parse_date_iso(raw.get("DEBAR_FROM_DATE"))
    except ValueError as exc:
        raise MapperError("DEBAR_FROM_DATE", str(exc)) from exc

    try:
        end_date = parse_date_iso(raw.get("DEBAR_TO_DATE"))
    except ValueError as exc:
        raise MapperError("DEBAR_TO_DATE", str(exc)) from exc

    return CanonicalRecord(
        source_system="worldbank",
        source_url=_SOURCE_URL,
        source_record_id=record_id,
        entity_name=entity_name,
        country=raw.get("COUNTRY_NAME") or None,
        reason=raw.get("DEBAR_REASON") or None,
        effective_date=effective_date,
        end_date=end_date,
        reference_id=None,
        raw_payload=dict(raw),
    )
