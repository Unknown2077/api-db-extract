from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class CanonicalRecord(BaseModel):
    source_system: Literal["inaproc", "worldbank"]
    source_url: str
    source_record_id: str
    entity_name: str
    country: str | None = None
    reason: str | None = None
    # Normalised to ISO 8601 YYYY-MM-DD by mapper; None if absent or unparseable
    effective_date: str | None = None
    end_date: str | None = None
    reference_id: str | None = None
    # Stored as plain dict (JSON object), never as a JSON string
    raw_payload: dict[str, object]
    ingested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
