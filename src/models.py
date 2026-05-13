from datetime import datetime, timezone
from typing import Literal, Optional

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
    ingested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InaprocBlacklistRegistry(BaseModel):
    """
    Pydantic model for Blacklist Detail Records based on Indonesian
    procurement (LPSE/LKPP) violation data.
    """

    id: str = Field(..., description="Unique identifier for the blacklist entry record")
    sk_number: str = Field(..., description="The official decree number for the blacklist")
    sk_number_status_based: Optional[str] = Field(
        None, description="Status-specific decree number tracking"
    )
    status: str = Field(..., description="Current status of the record (e.g., PUBLISHED)")
    start_date: datetime = Field(..., description="Effective start date of the blacklist period")
    expired_date: datetime = Field(..., description="End date of the blacklist period")

    # Tender Information
    tender_name: Optional[str] = Field(
        None, description="Name of the construction or procurement package"
    )
    tender_pagu: Optional[int] = Field(None, description="The ceiling budget (Pagu) for the tender")
    tender_hps: Optional[int] = Field(None, description="Self-Estimated Price (Harga Perkiraan Sendiri)")
    tender_budget_year: Optional[int] = Field(None, description="Fiscal year of the project budget")
    tender_category: Optional[str] = Field(None, description="Type of procurement")

    # Provider Information
    provider_name: str = Field(..., description="The registered name of the blacklisted vendor")
    provider_address: Optional[str] = Field(
        None, description="Physical address of the provider's office"
    )

    # Legal & Violation Details
    document_name: Optional[str] = Field(None, description="Title of the legal basis or finding document")
    violation_name: Optional[str] = Field(None, description="Regulation reference code")
    violation_description: Optional[str] = Field(
        None, description="Specific description of the non-compliance"
    )
    violation_month: Optional[int] = Field(None, description="Month duration of the penalty")
    violation_year: Optional[int] = Field(None, description="Year duration of the penalty")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "vBRW3dILpvJl6SXMI1fQe99oquNK5t",
                "sk_number": "HK.02.03/D.VII/388/2026",
                "status": "PUBLISHED",
                "tender_pagu": 130036600000,
                "provider_name": "JAYA SEMANGGI ENJINIRING",
                "violation_year": 2,
            }
        }


class WorldBankDebarment(BaseModel):
    """
    Pydantic model representing a World Bank Sanctioned Entity.
    Based on Section III.A of Bank Procedure: Sanctions Proceedings.
    """
    supp_id: int = Field(..., description="Internal system identifier")
    supp_name: str = Field(..., description="Name of debarred firm/individual")
    supp_type_code: Optional[str] = None
    land1: Optional[str] = Field(None, description="ISO Country Code")
    country_name: Optional[str] = None
    supp_city: Optional[str] = None
    supp_addr: Optional[str] = None
    
    # Ineligibility Period
    debar_from_date: Optional[datetime] = None
    debar_to_date: Optional[datetime] = None
    
    # Grounds and Status
    debar_reason: Optional[str] = Field(None, description="Grounds for sanction")
    supp_elig_stat: Optional[str] = None
    ineligibly_status: Optional[str] = None
    add_supp_info: Optional[str] = Field(None, description="Additional notes or DBA names")
    last_refresh_date: datetime

    class Config:
        from_attributes = True