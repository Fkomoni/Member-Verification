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


def _extract_provider_record(prognosis_data: dict) -> dict:
    """
    Extract provider fields from Prognosis ProviderLogIn response.

    Response shape:
    {"status": 200, "result": [{ "Id": "...", "provider_id": 8325,
      "surname": "...", "firstname": "...", "Email": "...",
      "ProviderStatus": "ACTIVE", ... }], "ErrorMessage": ""}
    """
    # Result is an array — take first record
    results = prognosis_data.get("result") or prognosis_data.get("Result") or []
    if isinstance(results, list) and len(results) > 0:
        rec = results[0]
    elif isinstance(prognosis_data, dict) and "provider_id" in prognosis_data:
        rec = prognosis_data
    else:
        return {}

    surname = rec.get("surname") or ""
    firstname = rec.get("firstname") or ""
    name = f"{firstname} {surname}".strip() or surname or "Unknown Provider"

    return {
        "name": name,
        "prognosis_provider_id": str(rec.get("provider_id") or ""),
        "prognosis_user_id": str(rec.get("User_id") or ""),
        "prognosis_uuid": rec.get("Id") or "",
        "email": rec.get("Email") or "",
        "status": rec.get("ProviderStatus") or "ACTIVE",
        "state_id": rec.get("StateID"),
        "city_id": rec.get("CityID"),
    }


def _upsert_provider(db: Session, email: str, password: str, prognosis_data: dict) -> Provider:
    """Create or update a provider record from Prognosis response data."""
    provider = db.query(Provider).filter(Provider.email == email).first()

    data = _extract_provider_record(prognosis_data)
    name = data.get("name") or email.split("@")[0]
    prognosis_id = data.get("prognosis_provider_id") or ""
    is_active = data.get("status", "").upper() == "ACTIVE"

    # Determine role based on admin email list
    admin_emails = ["f-komoni-mbaekwe@leadway.com", "e-ibekeh@leadway.com"]
    role = "admin" if email.lower() in [e.lower() for e in admin_emails] else "provider"

    if provider:
        # Update existing
        provider.hashed_password = hash_password(password)
        provider.is_active = is_active
        provider.role = role
        if name:
            provider.name = name
        if prognosis_id:
            provider.prognosis_provider_id = prognosis_id
    else:
        # Create new
        provider = Provider(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            prognosis_provider_id=prognosis_id or "pending",
            is_active=is_active,
            role=role,
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
        role=getattr(provider, "role", "provider") or "provider",
    )
