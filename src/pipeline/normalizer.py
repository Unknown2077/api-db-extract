"""Normalizer — raw dict → CanonicalRecord dispatch only.

Dead-letter handling for mapper errors is the orchestrator's responsibility.
"""
from src.errors import MapperError
from src.mappers.inaproc_mapper import map_inaproc
from src.mappers.worldbank_mapper import map_worldbank
from src.types import CanonicalRecord

_MAPPERS = {
    "inaproc": map_inaproc,
    "worldbank": map_worldbank,
}


def normalize(raw: dict, source: str) -> CanonicalRecord:
    """Map a raw dict to CanonicalRecord.

    Raises:
        MapperError: If mapping fails (missing field, bad date, etc.)
        KeyError: If source is not registered.
    """
    mapper = _MAPPERS.get(source)
    if mapper is None:
        raise KeyError(f"No mapper registered for source: {source!r}")
    return mapper(raw)
