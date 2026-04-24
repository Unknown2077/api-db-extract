"""Unit tests: worldbank_mapper."""
import pytest

from src.errors import MapperError
from src.mappers.worldbank_mapper import map_worldbank


def _raw(**kwargs) -> dict:
    base = {
        "SUPP_ID": "329186",
        "SUPP_NAME": "Acme Corp",
        "COUNTRY_NAME": "Kenya",
        "DEBAR_FROM_DATE": "2022-06-15",
        "DEBAR_TO_DATE": "2025-06-14",
        "DEBAR_REASON": "Fraud",
    }
    base.update(kwargs)
    return base


def test_map_worldbank_happy_path():
    rec = map_worldbank(_raw())
    assert rec.source_system == "worldbank"
    assert rec.entity_name == "Acme Corp"
    assert rec.effective_date == "2022-06-15"
    assert rec.end_date == "2025-06-14"
    assert rec.country == "Kenya"
    assert rec.reason == "Fraud"
    assert rec.source_record_id == "329186"
    assert isinstance(rec.raw_payload, dict)


def test_map_worldbank_missing_firm_name():
    with pytest.raises(MapperError, match="SUPP_NAME"):
        map_worldbank(_raw(SUPP_NAME=""))


def test_map_worldbank_bad_from_date():
    with pytest.raises(MapperError, match="DEBAR_FROM_DATE"):
        map_worldbank(_raw(DEBAR_FROM_DATE="not-a-date"))


def test_map_worldbank_bad_to_date():
    with pytest.raises(MapperError, match="DEBAR_TO_DATE"):
        map_worldbank(_raw(DEBAR_TO_DATE="oops"))


def test_map_worldbank_null_optional_fields():
    rec = map_worldbank(_raw(COUNTRY_NAME=None, DEBAR_REASON=None, DEBAR_TO_DATE=""))
    assert rec.country is None
    assert rec.reason is None
    assert rec.end_date is None


def test_map_worldbank_record_id_deterministic():
    raw = _raw()
    rec1 = map_worldbank(raw)
    rec2 = map_worldbank(raw)
    assert rec1.source_record_id == rec2.source_record_id
