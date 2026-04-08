"""
Call Center API endpoints:
  POST /agent/login        – Agent authentication
  GET  /authorization/lookup-member  – Look up enrollee via Prognosis
  GET  /authorization/visit-types    – Get visit types for enrollee
  POST /authorization/generate       – Generate PA code
  GET  /authorization/codes          – List PA codes for agent
"""

import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.models import Agent, AuthorizationCode
from app.services import prognosis_client

router = APIRouter(tags=["call-center"])


# ── Agent auth dependency ────────────────────────────────────
from fastapi.security import OAuth2PasswordBearer

agent_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/agent/login", auto_error=False)


def get_current_agent(
    token: str = Depends(agent_oauth2),
    db: Session = Depends(get_db),
) -> Agent:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    agent_id = payload.get("sub")
    role = payload.get("role")
    if not agent_id or role != "agent":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    agent = db.query(Agent).filter(Agent.agent_id == uuid.UUID(agent_id)).first()
    if agent is None or not agent.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Agent not found or inactive")
    return agent


# ── Endpoints ────────────────────────────────────────────────

@router.post("/agent/login")
def agent_login(body: dict, db: Session = Depends(get_db)):
    email = body.get("email", "")
    password = body.get("password", "")

    agent = db.query(Agent).filter(Agent.email == email).first()
    if not agent or not verify_password(password, agent.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not agent.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    token = create_access_token(data={"sub": str(agent.agent_id), "role": "agent"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "agent_id": str(agent.agent_id),
        "agent_name": agent.name,
        "role": agent.role,
    }


@router.get("/authorization/lookup-member")
async def lookup_member(
    enrollee_id: str = Query(...),
    agent: Agent = Depends(get_current_agent),
):
    """Look up enrollee via Prognosis and return profile."""
    biodata_result = await prognosis_client.get_enrollee_biodata(enrollee_id)

    if not biodata_result["success"] or not biodata_result["data"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=biodata_result.get("reason") or "Enrollee not found",
        )

    d = biodata_result["data"]
    return {
        "found": True,
        "enrollee_id": d.get("Member_EnrolleeID") or enrollee_id,
        "name": (
            d.get("Member_CustomerName")
            or f"{d.get('Member_FirstName', '')} {d.get('Member_othernames', '')} {d.get('Member_Surname', '')}".strip()
            or "Unknown"
        ),
        "gender": d.get("Member_Gender"),
        "dob": d.get("Member_DateOfBirth"),
        "phone": d.get("Member_Phone_One"),
        "email": d.get("Member_EmailAddress_One"),
        "company": d.get("Client_ClientName"),
        "plan": d.get("Member_Plan"),
        "plan_category": d.get("Plan_Category"),
        "scheme_name": d.get("client_schemename") or d.get("Product_schemeType"),
        "policy_no": d.get("Client_PolicyNumber"),
        "member_status": d.get("Member_MemberStatus_Description"),
        "member_type": d.get("Member_Membertype"),
        "cif_number": str(d.get("Member_MemberUniqueID") or ""),
        "scheme_id": str(d.get("Member_PlanID") or ""),
        "expiry_date": d.get("Member_ExpiryDate"),
        "effective_date": d.get("Member_Effectivedate"),
    }


@router.get("/authorization/visit-types")
async def get_visit_types(
    cif: str = Query(...),
    scheme_id: str = Query(...),
    agent: Agent = Depends(get_current_agent),
):
    """Fetch visit/service types for an enrollee from Prognosis."""
    result = await prognosis_client.get_service_types(cif=cif, scheme_id=scheme_id)
    return {
        "success": result["success"],
        "reason": result.get("reason"),
        "service_types": result.get("service_types", []),
    }


def _generate_pa_code() -> str:
    """Generate a unique PA code like PA-XXXX-XXXX."""
    chars = string.ascii_uppercase + string.digits
    part1 = "".join(random.choices(chars, k=4))
    part2 = "".join(random.choices(chars, k=4))
    return f"PA-{part1}-{part2}"


@router.post("/authorization/generate")
def generate_authorization_code(
    body: dict,
    db: Session = Depends(get_db),
    agent: Agent = Depends(get_current_agent),
):
    """Generate a pre-authorization code for a member visit."""
    enrollee_id = body.get("enrollee_id")
    enrollee_name = body.get("enrollee_name", "Unknown")
    visit_type_id = body.get("visit_type_id")
    visit_type_name = body.get("visit_type_name", "")
    approved_amount = body.get("approved_amount", 0.0)
    cif_number = body.get("cif_number", "")
    scheme_id = body.get("scheme_id", "")
    notes = body.get("notes", "")

    if not enrollee_id or not visit_type_id:
        raise HTTPException(status_code=400, detail="enrollee_id and visit_type_id are required")

    code = _generate_pa_code()
    # Ensure unique
    while db.query(AuthorizationCode).filter(AuthorizationCode.code == code).first():
        code = _generate_pa_code()

    auth_code = AuthorizationCode(
        code=code,
        enrollee_id=enrollee_id,
        enrollee_name=enrollee_name,
        visit_type_id=int(visit_type_id),
        visit_type_name=visit_type_name,
        approved_amount=float(approved_amount),
        cif_number=cif_number,
        scheme_id=scheme_id,
        notes=notes,
        status="ACTIVE",
        agent_id=agent.agent_id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
    )
    db.add(auth_code)
    db.commit()
    db.refresh(auth_code)

    return {
        "code_id": str(auth_code.code_id),
        "code": auth_code.code,
        "enrollee_id": auth_code.enrollee_id,
        "enrollee_name": auth_code.enrollee_name,
        "visit_type_name": auth_code.visit_type_name,
        "approved_amount": auth_code.approved_amount,
        "status": auth_code.status,
        "created_at": auth_code.created_at.isoformat(),
        "expires_at": auth_code.expires_at.isoformat() if auth_code.expires_at else None,
    }


@router.get("/authorization/codes")
def list_authorization_codes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    agent: Agent = Depends(get_current_agent),
):
    """List PA codes generated by this agent."""
    codes = (
        db.query(AuthorizationCode)
        .filter(AuthorizationCode.agent_id == agent.agent_id)
        .order_by(AuthorizationCode.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "code_id": str(c.code_id),
            "code": c.code,
            "enrollee_id": c.enrollee_id,
            "enrollee_name": c.enrollee_name,
            "visit_type_name": c.visit_type_name,
            "approved_amount": c.approved_amount,
            "notes": c.notes,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
            "expires_at": c.expires_at.isoformat() if c.expires_at else None,
        }
        for c in codes
    ]


# ── Public member reimbursement endpoints (no auth required) ─

def _code_to_dict(c: AuthorizationCode) -> dict:
    return {
        "code_id": str(c.code_id),
        "code": c.code,
        "enrollee_id": c.enrollee_id,
        "enrollee_name": c.enrollee_name,
        "visit_type_id": c.visit_type_id,
        "visit_type_name": c.visit_type_name,
        "approved_amount": c.approved_amount,
        "notes": c.notes,
        "status": c.status,
        "created_at": c.created_at.isoformat(),
        "expires_at": c.expires_at.isoformat() if c.expires_at else None,
    }


@router.get("/reimbursement/lookup-code")
def lookup_pa_code(
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    """Public: look up a PA code and return enrollee name + details."""
    auth_code = (
        db.query(AuthorizationCode)
        .filter(AuthorizationCode.code == code.strip().upper())
        .first()
    )
    if not auth_code:
        raise HTTPException(status_code=404, detail="Authorization code not found")
    return _code_to_dict(auth_code)


@router.get("/reimbursement/active-codes")
def get_active_codes_for_enrollee(
    enrollee_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Public: get all ACTIVE PA codes for an enrollee ID."""
    codes = (
        db.query(AuthorizationCode)
        .filter(
            AuthorizationCode.enrollee_id == enrollee_id.strip(),
            AuthorizationCode.status == "ACTIVE",
        )
        .order_by(AuthorizationCode.created_at.desc())
        .all()
    )
    return [_code_to_dict(c) for c in codes]


@router.post("/reimbursement/submit")
async def submit_reimbursement(
    body: dict,
    db: Session = Depends(get_db),
):
    """Public: submit a reimbursement claim against a PA code, then send to Prognosis."""
    code = body.get("code", "").strip().upper()
    claim_amount = float(body.get("claim_amount", 0))

    auth_code = (
        db.query(AuthorizationCode)
        .filter(AuthorizationCode.code == code)
        .first()
    )
    if not auth_code:
        raise HTTPException(status_code=404, detail="Authorization code not found")
    if auth_code.status != "ACTIVE":
        raise HTTPException(status_code=400, detail=f"Code is {auth_code.status}, not ACTIVE")
    if claim_amount > auth_code.approved_amount:
        raise HTTPException(
            status_code=400,
            detail=f"Claim amount (NGN {claim_amount:,.2f}) exceeds approved amount (NGN {auth_code.approved_amount:,.2f})",
        )

    # Build claims batch payload for Prognosis AddClaim API
    claims_payload = {
        "cifnumber": auth_code.cif_number or "",
        "schemeid": auth_code.scheme_id or "",
        "dateofservice": body.get("visit_date", ""),
        "placeofservice": body.get("provider_name", ""),
        "claim_amount": str(claim_amount),
        "claimcurrencyid": "37",
        "claimReferenceInvoiceReceiptNumber": auth_code.code,
        "NumberOfClaims": "1",
        "claimRemarks": body.get("remarks", ""),
        "ClaimDocuments": body.get("claim_documents", []),
        "PaymentMode": "Bank",
        "BankName": body.get("bank_name", ""),
        "bank_id": "",
        "AccountName": body.get("account_name", ""),
        "AccountNumber": body.get("account_number", ""),
    }

    # Submit to Prognosis AddClaim API
    claims_result = await prognosis_client.create_claim(claims_payload)

    # Mark code as USED regardless of API result
    auth_code.status = "USED"
    db.commit()

    return {
        "success": True,
        "message": "Reimbursement claim submitted successfully",
        "code": auth_code.code,
        "enrollee_name": auth_code.enrollee_name,
        "visit_type_name": auth_code.visit_type_name,
        "approved_amount": auth_code.approved_amount,
        "claim_amount": claim_amount,
        "provider_name": body.get("provider_name", ""),
        "visit_date": body.get("visit_date", ""),
        "reason_for_visit": body.get("reason_for_visit", ""),
        "prognosis_claim": claims_result,
    }


@router.post("/reimbursement/validate-bank")
def validate_bank_account(body: dict):
    """
    Validate bank account number against name.
    TODO: Integrate with Paystack Resolve Account API:
    GET https://api.paystack.co/bank/resolve?account_number=XXX&bank_code=XXX
    Headers: Authorization: Bearer SECRET_KEY
    """
    account_number = body.get("account_number", "")
    bank_name = body.get("bank_name", "")

    if not account_number or not bank_name:
        return {"validated": False, "reason": "Account number and bank name required"}

    # TODO: Replace with Paystack API call
    # For now, return manual validation mode
    return {
        "validated": True,
        "account_name": "",  # Will be populated by Paystack
        "message": "Manual entry mode — Paystack integration pending",
    }
