"""
Agent authentication — login for call-center agents, claims officers, and admins.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import Agent
from app.schemas.schemas import AgentLoginRequest, AgentTokenResponse

router = APIRouter(prefix="/agent", tags=["agent-auth"])


@router.post("/login", response_model=AgentTokenResponse)
def agent_login(body: AgentLoginRequest, db: Session = Depends(get_db)):
    """Authenticate an agent and return a JWT token."""
    agent = db.query(Agent).filter(Agent.email == body.email).first()
    if not agent or not verify_password(body.password, agent.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token = create_access_token(
        data={
            "sub": str(agent.agent_id),
            "type": "agent",
            "role": agent.role,
            "name": agent.name,
        }
    )

    return AgentTokenResponse(
        access_token=token,
        agent_id=agent.agent_id,
        agent_name=agent.name,
        role=agent.role,
    )


@router.post("/seed", status_code=201, tags=["agent-auth"])
def seed_agent(db: Session = Depends(get_db)):
    """
    DEV ONLY: Create a default call-center agent for testing.
    Remove or protect this endpoint in production.
    """
    existing = db.query(Agent).filter(Agent.email == "agent@leadwayhealth.com").first()
    if existing:
        return {"message": "Seed agent already exists", "agent_id": str(existing.agent_id)}

    agent = Agent(
        name="Test Agent",
        email="agent@leadwayhealth.com",
        hashed_password=hash_password("agent123"),
        role="call_center",
    )
    db.add(agent)

    # Also seed a claims officer
    claims_officer = Agent(
        name="Claims Officer",
        email="claims@leadwayhealth.com",
        hashed_password=hash_password("claims123"),
        role="claims_officer",
    )
    db.add(claims_officer)

    # And an admin
    admin = Agent(
        name="Admin User",
        email="admin@leadwayhealth.com",
        hashed_password=hash_password("admin123"),
        role="admin",
    )
    db.add(admin)

    db.commit()
    return {
        "message": "Seed agents created",
        "agents": [
            {"email": "agent@leadwayhealth.com", "role": "call_center", "password": "agent123"},
            {"email": "claims@leadwayhealth.com", "role": "claims_officer", "password": "claims123"},
            {"email": "admin@leadwayhealth.com", "role": "admin", "password": "admin123"},
        ],
    }
