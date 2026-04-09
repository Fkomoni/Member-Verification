"""
POST /login – Provider authentication.

Flow:
  1. Try Prognosis ProviderLogIn API (if configured)
  2. On Prognosis success → upsert provider in local DB → issue local JWT
  3. On Prognosis failure/unavailable → fall back to local DB auth
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import Provider
from app.schemas.schemas import LoginRequest, TokenResponse
from app.services.prognosis_provider_auth import authenticate_provider

log = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


def _upsert_provider(db: Session, email: str, password: str, prognosis_data: dict) -> Provider:
    """Create or update a provider record from Prognosis response data."""
    provider = db.query(Provider).filter(Provider.email == email).first()

    # Extract fields from Prognosis response — adjust keys when live response is confirmed
    # Common patterns: providerId/ProviderId, providerName/ProviderName, etc.
    data = prognosis_data if isinstance(prognosis_data, dict) else {}
    name = (
        data.get("providerName") or data.get("ProviderName") or
        data.get("name") or data.get("Name") or
        data.get("facilityName") or data.get("FacilityName") or
        email.split("@")[0]
    )
    prognosis_id = str(
        data.get("providerId") or data.get("ProviderId") or
        data.get("providerCode") or data.get("ProviderCode") or
        data.get("id") or data.get("Id") or ""
    )
    location = (
        data.get("location") or data.get("Location") or
        data.get("address") or data.get("Address") or ""
    )

    if provider:
        # Update existing
        provider.hashed_password = hash_password(password)
        provider.is_active = True
        if name:
            provider.name = name
        if prognosis_id:
            provider.prognosis_provider_id = prognosis_id
        if location:
            provider.location = location
    else:
        # Create new
        provider = Provider(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            prognosis_provider_id=prognosis_id or "pending",
            location=location or None,
            is_active=True,
        )
        db.add(provider)

    db.commit()
    db.refresh(provider)
    return provider


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    # ── Try Prognosis API first ──────────────────────
    prognosis_data = await authenticate_provider(body.email, body.password)

    if prognosis_data:
        # Prognosis confirmed — upsert local record
        provider = _upsert_provider(db, body.email, body.password, prognosis_data)
        log.info("Provider %s authenticated via Prognosis", body.email)
    else:
        # ── Fall back to local DB ────────────────────
        provider = db.query(Provider).filter(Provider.email == body.email).first()
        if not provider or not verify_password(body.password, provider.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        log.info("Provider %s authenticated via local DB (Prognosis unavailable)", body.email)

    if not provider.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token = create_access_token(data={"sub": str(provider.provider_id)})
    return TokenResponse(
        access_token=token,
        provider_id=provider.provider_id,
        provider_name=provider.name,
        prognosis_provider_id=provider.prognosis_provider_id,
    )
