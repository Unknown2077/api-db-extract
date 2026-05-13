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
from src.models import CanonicalRecord, InaprocBlacklistRegistry
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

def map_inaproc_blacklist_registry(raw: dict) -> InaprocBlacklistRegistry:
    # Safely extract sub-dictionaries
    tender = raw.get("tender", {})
    if not tender:
        tender = {}
    provider = raw.get("provider", {})
    if not provider:
        provider = {}
    document = raw.get("document", {})
    if not document:
        document = {}
    violation = raw.get("violation", {})
    if not violation:
        violation = {}

    return InaprocBlacklistRegistry(
        # Root level fields
        id=raw.get("id"),
        sk_number=raw.get("skNumber"),
        sk_number_status_based=raw.get("skNumberStatusBased"),
        status=raw.get("status"),
        start_date=raw.get("startDate"),
        expired_date=raw.get("expiredDate"),

        # Tender nested fields
        tender_name=tender.get("name"),
        tender_pagu=tender.get("pagu"),
        tender_hps=tender.get("hps"),
        tender_budget_year=tender.get("budgetYear"),
        tender_category=tender.get("category"),

        # Provider nested fields
        provider_name=provider.get("name"),
        provider_address=provider.get("address"),

        # Document nested fields
        document_name=document.get("name"),

        # Violation nested fields
        violation_name=violation.get("name"),
        violation_description=violation.get("description"),
        # violation_month=violation.get("month"),
        # violation_year=violation.get("year")
    )