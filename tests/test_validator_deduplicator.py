"""Unit tests: validator and deduplicator."""
import pytest

from src.mappers.inaproc_mapper import map_inaproc
from src.pipeline.deduplicator import deduplicate
from src.pipeline.validator import validate
from src.types import CanonicalRecord


def _record(**kwargs) -> CanonicalRecord:
    base = dict(
        source_system="inaproc",
        source_url="https://example.com",
        source_record_id="id-1",
        entity_name="PT Test",
        raw_payload={"id": "id-1"},
    )
    base.update(kwargs)
    return CanonicalRecord(**base)


# --- validator ---

def test_valid_record_passes():
    is_valid, reason = validate(_record())
    assert is_valid is True
    assert reason is None


def test_missing_entity_name_fails():
    rec = _record(entity_name="")
    is_valid, reason = validate(rec)
    assert is_valid is False
    assert "entity_name" in reason


def test_missing_source_record_id_fails():
    rec = _record(source_record_id="")
    is_valid, reason = validate(rec)
    assert is_valid is False


def test_empty_raw_payload_fails():
    rec = _record(raw_payload={})
    # raw_payload={} is falsy — treated as missing
    is_valid, _ = validate(rec)
    assert is_valid is False


# --- deduplicator ---

def test_deduplicate_removes_exact_duplicates():
    r1 = _record(source_record_id="id-1")
    r2 = _record(source_record_id="id-1")
    r3 = _record(source_record_id="id-2")
    unique, count = deduplicate([r1, r2, r3])
    assert len(unique) == 2
    assert count == 1


def test_deduplicate_different_source_systems_not_deduped():
    r1 = _record(source_system="inaproc", source_record_id="x")
    r2 = _record(source_system="worldbank", source_record_id="x")
    unique, count = deduplicate([r1, r2])
    assert len(unique) == 2
    assert count == 0


def test_deduplicate_empty_list():
    unique, count = deduplicate([])
    assert unique == []
    assert count == 0


def test_deduplicate_preserves_first_occurrence():
    r1 = _record(source_record_id="id-1", entity_name="First")
    r2 = _record(source_record_id="id-1", entity_name="Second")
    unique, _ = deduplicate([r1, r2])
    assert unique[0].entity_name == "First"
