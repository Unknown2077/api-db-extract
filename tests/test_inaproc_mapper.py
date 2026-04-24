"""Unit tests: inaproc_mapper (real GraphQL schema)."""
import pytest

from src.errors import MapperError
from src.mappers.inaproc_mapper import map_inaproc


def _raw(**kwargs) -> dict:
    base = {
        "id": "abc123",
        "skNumber": "SK-001/2023",
        "skNumberStatusBased": "SK-001/2023-A",
        "status": "active",
        "startDate": "2023-01-15",
        "expiredDate": "2025-01-14",
        "publishDate": "2023-01-16",
        "publishDurationInMinutes": 1440,
        "statusUpdatedAt": "2023-01-16T08:00:00Z",
        "provider": {
            "id": "prov-1",
            "name": "PT Contoh Jaya",
            "npwp": "01.234.567.8-901.000",
            "address": "Jl. Contoh No. 1",
            "additionalAddress": None,
        },
        "tender": {
            "id": "tender-1",
            "name": "Pengadaan Barang",
            "packageId": "pkg-1",
            "pagu": 500000000,
            "hps": 480000000,
            "budgetYear": 2023,
            "category": "Barang",
        },
        "document": {
            "id": "doc-1",
            "name": "SK_Blacklist.pdf",
            "blacklistId": "abc123",
            "additionalInfo": None,
        },
        "correspondence": {
            "lpse": {"id": "lpse-1", "name": "LPSE Kota X"},
            "kldi": {"id": "kldi-1", "name": "KLDI Y"},
            "satker": {"id": "sat-1", "name": "Satker Z"},
        },
        "violation": {
            "id": "viol-1",
            "name": "Manipulasi dokumen",
            "description": "Memalsukan dokumen penawaran",
            "month": 1,
            "year": 2023,
        },
    }
    base.update(kwargs)
    return base


def test_map_inaproc_happy_path():
    rec = map_inaproc(_raw())
    assert rec.source_system == "inaproc"
    assert rec.source_record_id == "abc123"
    assert rec.entity_name == "PT Contoh Jaya"
    assert rec.effective_date == "2023-01-15"
    assert rec.end_date == "2025-01-14"
    assert rec.country == "Indonesia"
    assert rec.reason == "Manipulasi dokumen"
    assert rec.reference_id == "SK-001/2023"
    assert isinstance(rec.raw_payload, dict)


def test_map_inaproc_missing_id():
    with pytest.raises(MapperError, match="id"):
        map_inaproc(_raw(id=""))


def test_map_inaproc_missing_provider_name():
    with pytest.raises(MapperError, match="provider.name"):
        map_inaproc(_raw(provider={"id": "x", "name": "", "npwp": "", "address": "", "additionalAddress": None}))


def test_map_inaproc_missing_provider_entirely():
    with pytest.raises(MapperError, match="provider.name"):
        map_inaproc(_raw(provider=None))


def test_map_inaproc_bad_start_date():
    with pytest.raises(MapperError, match="startDate"):
        map_inaproc(_raw(startDate="not-a-date"))


def test_map_inaproc_bad_expired_date():
    with pytest.raises(MapperError, match="expiredDate"):
        map_inaproc(_raw(expiredDate="oops"))


def test_map_inaproc_null_optional_fields():
    rec = map_inaproc(_raw(violation=None, skNumber=None, expiredDate=None))
    assert rec.reason is None
    assert rec.reference_id is None
    assert rec.end_date is None


def test_map_inaproc_violation_fallback_to_description():
    rec = map_inaproc(_raw(violation={"id": "v1", "name": None, "description": "Detailed reason", "month": 1, "year": 2023}))
    assert rec.reason == "Detailed reason"


def test_map_inaproc_raw_payload_is_dict():
    raw = _raw()
    rec = map_inaproc(raw)
    assert rec.raw_payload == raw
