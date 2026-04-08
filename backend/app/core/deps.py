"""FastAPI dependency injection helpers."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import Agent, Provider

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")
agent_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/agent/login")


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


def get_current_agent(
    token: str = Depends(agent_oauth2_scheme),
    db: Session = Depends(get_db),
) -> Agent:
    """Decode JWT and return the authenticated Agent, or 401."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify this is an agent token
    if payload.get("type") != "agent":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    agent_id = payload.get("sub")
    if agent_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    agent = (
        db.query(Agent)
        .filter(Agent.agent_id == uuid.UUID(agent_id))
        .first()
    )
    if agent is None or not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found or inactive",
        )

    return agent


def require_role(*allowed_roles: str):
    """
    Dependency factory: ensures the current agent has one of the allowed roles.
    Usage: Depends(require_role("call_center", "admin"))
    """

    def _check(agent: Agent = Depends(get_current_agent)) -> Agent:
        if agent.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{agent.role}' is not authorized for this action",
            )
        return agent

    return _check
