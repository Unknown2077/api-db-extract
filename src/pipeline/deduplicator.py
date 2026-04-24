"""Deduplicator — within-run dedup by (source_system, source_record_id)."""
from src.types import CanonicalRecord


def deduplicate(records: list[CanonicalRecord]) -> tuple[list[CanonicalRecord], int]:
    """Remove duplicates within the current batch.

    Returns:
        (unique_records, deduped_count)
    """
    seen: set[tuple[str, str]] = set()
    unique: list[CanonicalRecord] = []

    for record in records:
        key = (record.source_system, record.source_record_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)

    return unique, len(records) - len(unique)
