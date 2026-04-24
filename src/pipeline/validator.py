"""Validator — checks canonical record required fields.

Returns (is_valid, reason). Dead-letter routing done by orchestrator.
"""
from src.types import CanonicalRecord

_REQUIRED = ("source_system", "source_record_id", "entity_name", "raw_payload", "ingested_at")


def validate(record: CanonicalRecord) -> tuple[bool, str | None]:
    """Check required fields are present and non-empty.

    Returns:
        (True, None) if valid.
        (False, reason) if invalid.
    """
    for field in _REQUIRED:
        value = getattr(record, field, None)
        if not value and value != 0:
            return False, f"Required field '{field}' is missing or empty"
    return True, None
