"""POST /login – Provider authentication."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, verify_password
from backend.app.models.models import Provider
from backend.app.schemas.schemas import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    provider = db.query(Provider).filter(Provider.email == body.email).first()
    if not provider or not verify_password(body.password, provider.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not provider.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token = create_access_token(data={"sub": str(provider.provider_id)})
    return TokenResponse(
        access_token=token,
        provider_id=provider.provider_id,
        provider_name=provider.name,
        prognosis_provider_id=provider.prognosis_provider_id,
    )
