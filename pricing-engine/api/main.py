"""
Leadway Householder Pricing Engine API.

FastAPI backend using official Leadway rate tables.
Separate Building vs Content pricing with additional coverages.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from engine import ClientType, CoverType, Location, RiskProfile, calculate_premium

app = FastAPI(
    title="Leadway Householder Pricing Engine",
    description="Premium calculation using official Leadway rate tables",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


class QuoteRequest(BaseModel):
    client_type: str = Field(..., description="'corporate' or 'individual'")
    building_sum_insured: float = Field(default=0, ge=0, description="Building sum insured (NGN)")
    content_sum_insured: float = Field(default=0, ge=0, description="Content sum insured (NGN)")
    location: str = Field(..., description="Location")
    cover_type: str = Field(default="standard", description="Cover tier")
    include_building: bool = Field(default=True)
    include_content: bool = Field(default=True)
    include_accidental_damage: bool = Field(default=False)
    include_all_risks: bool = Field(default=False)
    include_personal_accident: bool = Field(default=False)
    include_alt_accommodation: bool = Field(default=False)
    building_age_years: int = Field(default=0, ge=0)
    has_security: bool = Field(default=False)
    has_fire_extinguisher: bool = Field(default=False)
    claims_history_count: int = Field(default=0, ge=0)
    policy_duration_months: int = Field(default=12, ge=3, le=12)


class QuoteResponse(BaseModel):
    building_premium: float
    content_premium: float
    accidental_damage_premium: float
    all_risks_premium: float
    personal_accident_premium: float
    alt_accommodation_premium: float
    base_premium: float
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
    coverages: list[str]


@app.get("/")
async def root():
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Leadway Householder Pricing Engine API", "docs": "/docs"}


@app.post("/api/quote", response_model=QuoteResponse)
async def generate_quote(request: QuoteRequest):
    try:
        client_type = ClientType(request.client_type.lower())
    except ValueError:
        raise HTTPException(400, f"Invalid client_type: {request.client_type}")

    try:
        location = Location(request.location.lower())
    except ValueError:
        raise HTTPException(400, f"Invalid location: {request.location}")

    try:
        cover_type = CoverType(request.cover_type.lower())
    except ValueError:
        raise HTTPException(400, f"Invalid cover_type: {request.cover_type}")

    if request.building_sum_insured == 0 and request.content_sum_insured == 0:
        raise HTTPException(400, "At least one sum insured must be greater than zero.")

    risk = RiskProfile(
        client_type=client_type,
        building_sum_insured=request.building_sum_insured,
        content_sum_insured=request.content_sum_insured,
        location=location,
        cover_type=cover_type,
        include_building=request.include_building,
        include_content=request.include_content,
        include_accidental_damage=request.include_accidental_damage,
        include_all_risks=request.include_all_risks,
        include_personal_accident=request.include_personal_accident,
        include_alt_accommodation=request.include_alt_accommodation,
        building_age_years=request.building_age_years,
        has_security=request.has_security,
        has_fire_extinguisher=request.has_fire_extinguisher,
        claims_history_count=request.claims_history_count,
        policy_duration_months=request.policy_duration_months,
    )

    result = calculate_premium(risk)

    coverages = []
    if request.include_building:
        coverages.append("Building (Fire & Special Perils)")
    if request.include_content:
        coverages.append("Content (Fire, Burglary & Special Perils)")
    if request.include_accidental_damage:
        coverages.append("Accidental Damage")
    if request.include_all_risks:
        coverages.append("All Risks Extension")
    if request.include_personal_accident:
        coverages.append("Personal Accident")
    if request.include_alt_accommodation:
        coverages.append("Alternative Accommodation")

    return QuoteResponse(
        building_premium=result.building_premium,
        content_premium=result.content_premium,
        accidental_damage_premium=result.accidental_damage_premium,
        all_risks_premium=result.all_risks_premium,
        personal_accident_premium=result.personal_accident_premium,
        alt_accommodation_premium=result.alt_accommodation_premium,
        base_premium=result.base_premium,
        location_adjustment=result.location_adjustment,
        cover_type_adjustment=result.cover_type_adjustment,
        claims_loading=result.claims_loading,
        security_discount=result.security_discount,
        fire_equipment_discount=result.fire_equipment_discount,
        duration_adjustment=result.duration_adjustment,
        gross_premium=result.gross_premium,
        commission=result.commission,
        net_premium=result.net_premium,
        rate_per_mille=result.rate_per_mille,
        client_type=client_type.value,
        coverages=coverages,
    )


@app.get("/api/rates")
async def get_rate_card():
    from engine.rates import (
        INDIVIDUAL_RATES, CORPORATE_RATES, CORPORATE_ADDITIONAL_RATES,
        LOCATION_FACTORS, MINIMUM_PREMIUMS, COMMISSION_RATES,
    )

    return {
        "individual_rates": INDIVIDUAL_RATES,
        "corporate_rates": CORPORATE_RATES,
        "corporate_additional": CORPORATE_ADDITIONAL_RATES,
        "location_factors": {k.value: v for k, v in LOCATION_FACTORS.items()},
        "minimum_premiums": {k.value: v for k, v in MINIMUM_PREMIUMS.items()},
        "commission_rates": {k.value: v for k, v in COMMISSION_RATES.items()},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
