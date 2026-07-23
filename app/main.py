"""
main.py

FastAPI application exposing a clean REST API on top of the legacy
Urja Meter Ops portal.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app.client import (
    urja_client,
    UrjaAuthError,
    UrjaNotFoundError,
    UrjaUpstreamError,
)
from app.models import (
    MeterListResponse,
    MeterSummary,
    MeterDetail,
    GeoLocation,
    ConsumptionResponse,
    ConsumptionReading,
    LoginResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: log into the legacy portal once so the session cookie is
    # ready before any request comes in.
    try:
        await urja_client.login()
    except UrjaAuthError as exc:
        # We don't crash the whole app -- individual endpoints will
        # attempt re-auth on demand -- but we log this loudly.
        print(f"[startup] WARNING: initial login failed: {exc}")
    yield
    # Shutdown: close the underlying HTTP session cleanly.
    await urja_client.close()


app = FastAPI(
    title="Flock Energy API",
    description="A clean REST API wrapper around the legacy Urja Meter Ops portal.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------- Error translation helper ----------------

def _handle_upstream_errors(exc: Exception):
    if isinstance(exc, UrjaNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, UrjaAuthError):
        raise HTTPException(status_code=502, detail=f"Upstream authentication failed: {exc}")
    if isinstance(exc, UrjaUpstreamError):
        raise HTTPException(status_code=503, detail=f"Upstream portal error: {exc}")
    raise HTTPException(status_code=500, detail=f"Internal error: {exc}")


# ---------------- Auth endpoint ----------------

@app.post("/api/v1/auth/login", response_model=LoginResponse, tags=["auth"])
async def login():
    """Force a (re-)login against the legacy portal."""
    try:
        await urja_client.login()
    except (UrjaAuthError, UrjaUpstreamError) as exc:
        _handle_upstream_errors(exc)
    return LoginResponse(authenticated=True, logged_in_at=urja_client.logged_in_at)


# ---------------- Meters endpoints ----------------

@app.get("/api/v1/meters", response_model=MeterListResponse, tags=["meters"])
async def list_meters(
    page: int = Query(default=1, ge=1, description="Page number, starting at 1"),
    q: str = Query(default="", description="Search by meter number or serial"),
):
    try:
        payload = await urja_client.get_meters(page=page, q=q)
    except (UrjaAuthError, UrjaUpstreamError) as exc:
        _handle_upstream_errors(exc)

    return MeterListResponse(
        data=[MeterSummary(**item) for item in payload.get("data", [])],
        total=payload.get("total", 0),
        page=payload.get("page", page),
        page_size=payload.get("pageSize", 20),
    )


@app.get("/api/v1/meters/{meter_id}", response_model=MeterDetail, tags=["meters"])
async def get_meter(meter_id: str):
    try:
        meter = await urja_client.get_meter_by_id(meter_id)
        if meter is None:
            raise HTTPException(status_code=404, detail=f"Meter '{meter_id}' not found")

        geo = await urja_client.get_geo(meter_id)
    except (UrjaAuthError, UrjaUpstreamError, UrjaNotFoundError) as exc:
        _handle_upstream_errors(exc)

    return MeterDetail(
        meter_id=meter["meterId"],
        serial_no=meter["serialNo"],
        make=meter["make"],
        phase_type=meter["phaseType"],
        status=meter.get("status"),
        dt=meter.get("dt"),
        location=GeoLocation(**geo) if geo else None,
    )


@app.get(
    "/api/v1/meters/{meter_id}/consumption",
    response_model=ConsumptionResponse,
    tags=["meters"],
)
async def get_consumption(meter_id: str):
    try:
        raw_readings = await urja_client.get_energy(meter_id)
    except (UrjaAuthError, UrjaUpstreamError, UrjaNotFoundError) as exc:
        _handle_upstream_errors(exc)

    readings = []
    for item in raw_readings:
        readings.append(
            ConsumptionReading(
                timestamp=datetime.strptime(item["timestamp"], "%d/%m/%Y %H:%M"),
                kwh=float(item["kwh"]),
                kvah=float(item["kvah"]),
                voltR=float(item["voltR"]),
            )
        )

    return ConsumptionResponse(
        meter_id=meter_id,
        readings=readings,
        count=len(readings),
    )


# ---------------- Root ----------------

@app.get("/", tags=["meta"])
async def root():
    return JSONResponse(
        {
            "service": "Flock Energy API",
            "docs": "/docs",
            "openapi": "/openapi.json",
        }
    )