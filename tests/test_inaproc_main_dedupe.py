"""Tests: inaproc dedupe by id (keep-latest) in main pipeline."""
from datetime import datetime, timezone

from src.main import _dedupe_inaproc_keep_latest
from src.models import InaprocBlacklistRegistry


def _reg(record_id: str, *, sk: str = "SK-1") -> InaprocBlacklistRegistry:
    return InaprocBlacklistRegistry(
        id=record_id,
        sk_number=sk,
        status="PUBLISHED",
        start_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        expired_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
        provider_name="ACME",
    )


def test_dedupe_collapses_duplicate_ids():
    records = [
        _reg("a", sk="SK-first"),
        _reg("b"),
        _reg("a", sk="SK-last"),
    ]
    out = _dedupe_inaproc_keep_latest(records)
    assert len(out) == 2
    by_id = {r.id: r for r in out}
    assert by_id["a"].sk_number == "SK-last"
    assert by_id["b"].sk_number == "SK-1"


def test_dedupe_keeps_latest_occurrence_per_id():
    first = _reg("x", sk="OLD")
    second = _reg("x", sk="NEW")
    out = _dedupe_inaproc_keep_latest([first, second])
    assert len(out) == 1
    assert out[0].sk_number == "NEW"
    assert out[0] is second
