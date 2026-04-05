"""
Leadway Householder Pricing Engine API.

FastAPI backend serving premium calculations for
Corporate and Individual householder insurance.
"""

import sys
from pathlib import Path

# Add parent to path for engine imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional

from engine import (
    ClientType, CoverType, Peril, Location,
    RiskProfile, calculate_premium,
)

app = FastAPI(
    title="Leadway Householder Pricing Engine",
    description="Premium calculation API for Householder Insurance (Fire, Theft, Flood)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


class QuoteRequest(BaseModel):
    client_type: str = Field(..., description="'corporate' or 'individual'")
    sum_insured: float = Field(..., gt=0, description="Total sum insured in NGN")
    location: str = Field(..., description="Location: lagos, abuja, port_harcourt, ibadan, kaduna, other")
    cover_type: str = Field(default="standard", description="Cover tier: basic, bronze, silver, standard, gold, platinum")
    perils: list[str] = Field(default=["fire"], description="Perils to cover: fire, theft, flood")
    building_age_years: int = Field(default=0, ge=0, description="Age of building in years")
    has_security: bool = Field(default=False, description="Has security system installed")
    has_fire_extinguisher: bool = Field(default=False, description="Has fire extinguisher")
    claims_history_count: int = Field(default=0, ge=0, description="Number of claims in last 3 years")
    policy_duration_months: int = Field(default=12, ge=3, le=12, description="Policy duration in months")


class QuoteResponse(BaseModel):
    base_premium: float
    fire_premium: float
    theft_premium: float
    flood_premium: float
    location_adjustment: float
    cover_type_adjustment: float
    claims_loading: float
    security_discount: float
    fire_equipment_discount: float
    duration_adjustment: float
    gross_premium: float
    commission: float
    net_premium: float
    rate_per_mille: float
    client_type: str
    perils_covered: list[str]


@app.get("/")
async def root():
    """Serve the frontend."""
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Leadway Householder Pricing Engine API", "docs": "/docs"}


@app.post("/api/quote", response_model=QuoteResponse)
async def generate_quote(request: QuoteRequest):
    """Generate a premium quote for a householder policy."""

    try:
        client_type = ClientType(request.client_type.lower())
    except ValueError:
        raise HTTPException(400, f"Invalid client_type: {request.client_type}. Use 'corporate' or 'individual'.")

    try:
        location = Location(request.location.lower())
    except ValueError:
        raise HTTPException(400, f"Invalid location: {request.location}. Use: lagos, abuja, port_harcourt, ibadan, kaduna, other.")

    try:
        cover_type = CoverType(request.cover_type.lower())
    except ValueError:
        raise HTTPException(400, f"Invalid cover_type: {request.cover_type}. Use: basic, bronze, silver, standard, gold, platinum.")

    perils = []
    for p in request.perils:
        try:
            perils.append(Peril(p.lower()))
        except ValueError:
            raise HTTPException(400, f"Invalid peril: {p}. Use: fire, theft, flood.")

    if not perils:
        raise HTTPException(400, "At least one peril must be selected.")

    risk = RiskProfile(
        client_type=client_type,
        sum_insured=request.sum_insured,
        location=location,
        cover_type=cover_type,
        perils=perils,
        building_age_years=request.building_age_years,
        has_security=request.has_security,
        has_fire_extinguisher=request.has_fire_extinguisher,
        claims_history_count=request.claims_history_count,
        policy_duration_months=request.policy_duration_months,
    )

    result = calculate_premium(risk)

    rate_per_mille = (result.gross_premium / request.sum_insured) * 1000 if request.sum_insured > 0 else 0

    return QuoteResponse(
        base_premium=result.base_premium,
        fire_premium=result.fire_premium,
        theft_premium=result.theft_premium,
        flood_premium=result.flood_premium,
        location_adjustment=result.location_adjustment,
        cover_type_adjustment=result.cover_type_adjustment,
        claims_loading=result.claims_loading,
        security_discount=result.security_discount,
        fire_equipment_discount=result.fire_equipment_discount,
        duration_adjustment=result.duration_adjustment,
        gross_premium=result.gross_premium,
        commission=result.commission,
        net_premium=result.net_premium,
        rate_per_mille=round(rate_per_mille, 4),
        client_type=client_type.value,
        perils_covered=[p.value for p in perils],
    )


@app.get("/api/rates")
async def get_rate_card():
    """Return the current rate card for reference."""
    from engine.rates import (
        BASE_RATES, LOCATION_FACTORS, COVER_TYPE_MULTIPLIERS,
        MINIMUM_PREMIUMS, COMMISSION_RATES,
    )

    return {
        "base_rates_per_mille": {
            ct.value: {p.value: r for p, r in rates.items()}
            for ct, rates in BASE_RATES.items()
        },
        "location_factors": {k.value: v for k, v in LOCATION_FACTORS.items()},
        "cover_type_multipliers": {k.value: v for k, v in COVER_TYPE_MULTIPLIERS.items()},
        "minimum_premiums": {k.value: v for k, v in MINIMUM_PREMIUMS.items()},
        "commission_rates": {k.value: v for k, v in COMMISSION_RATES.items()},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
