"""FastAPI dependency injection helpers."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import Provider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


def get_current_provider(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Provider:
    """Decode JWT and return the authenticated Provider, or 401."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    provider_id = payload.get("sub")
    if provider_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    provider = db.query(Provider).filter(Provider.provider_id == uuid.UUID(provider_id)).first()
    if provider is None or not provider.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Provider not found or inactive")

    return provider


def get_admin_provider(
    provider: Provider = Depends(get_current_provider),
) -> Provider:
    """Require the authenticated provider to have admin role, or 403."""
    if getattr(provider, "role", "provider") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return provider
