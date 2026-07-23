"""
models.py

Pydantic models (schemas) for both:
1. Data coming FROM the legacy Urja portal (raw shapes)
2. Data going OUT of our own REST API (clean, typed shapes)

Numbers-as-strings and DD/MM/YYYY timestamps from the legacy system are
normalized into proper types here.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------- Meter models ----------

class MeterSummary(BaseModel):
    """A single meter as returned by the legacy /portal/meters/search endpoint."""
    meter_id: str = Field(alias="meterId")
    serial_no: str = Field(alias="serialNo")
    make: str
    phase_type: str = Field(alias="phaseType")
    status: Optional[str] = None
    dt: Optional[str] = Field(default=None, alias="dt")

    class Config:
        populate_by_name = True


class MeterListResponse(BaseModel):
    """Our API's response shape for GET /api/v1/meters."""
    data: List[MeterSummary]
    total: int
    page: int
    page_size: int


# ---------- Consumption / energy models ----------

class ConsumptionReading(BaseModel):
    """
    One normalized consumption data point.

    Legacy format: {"timestamp": "23/06/2026 23:30", "kwh": "48438.74", ...}
    Normalized: real datetime object, real floats.
    """
    timestamp: datetime
    kwh: float
    kvah: float
    volt_r: float = Field(alias="voltR")

    class Config:
        populate_by_name = True


class ConsumptionResponse(BaseModel):
    meter_id: str
    readings: List[ConsumptionReading]
    count: int


# ---------- Geo models ----------

class GeoLocation(BaseModel):
    latitude: float
    longitude: float


# ---------- Combined meter detail ----------

class MeterDetail(BaseModel):
    meter_id: str
    serial_no: str
    make: str
    phase_type: str
    status: Optional[str] = None
    dt: Optional[str] = None
    location: Optional[GeoLocation] = None


# ---------- Auth models ----------

class LoginResponse(BaseModel):
    authenticated: bool
    logged_in_at: datetime


# ---------- Error model ----------

class ErrorResponse(BaseModel):
    detail: str