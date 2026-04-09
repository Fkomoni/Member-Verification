"""
Call Center API endpoints:
  POST /agent/login        – Agent authentication
  GET  /authorization/lookup-member  – Look up enrollee via Prognosis
  GET  /authorization/visit-types    – Get visit types for enrollee
  POST /authorization/generate       – Generate PA code
  GET  /authorization/codes          – List PA codes for agent
"""

import logging
import random
import string
import uuid
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.models import Agent, AuthorizationCode, ReimbursementClaim
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
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
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

    # Extract batch number from Prognosis response
    batch_number = None
    prognosis_status = None
    if claims_result.get("success") and claims_result.get("data"):
        prog_data = claims_result["data"]
        # Try common field names for batch/claim reference
        if isinstance(prog_data, dict):
            batch_number = (
                prog_data.get("BatchNumber")
                or prog_data.get("batchNumber")
                or prog_data.get("batch_number")
                or prog_data.get("ClaimBatchNo")
                or prog_data.get("claimBatchNo")
                or prog_data.get("ReferenceNumber")
                or prog_data.get("referenceNumber")
                or prog_data.get("ClaimID")
                or prog_data.get("claimId")
                or str(prog_data.get("result", ""))[:50] if prog_data.get("result") else None
            )
            prognosis_status = prog_data.get("Message") or prog_data.get("message") or "Submitted"
        elif isinstance(prog_data, str):
            batch_number = prog_data[:50]

    # Mark code as USED
    auth_code.status = "USED"

    # Save claim to database
    import json
    claim = ReimbursementClaim(
        pa_code=auth_code.code,
        enrollee_id=auth_code.enrollee_id,
        enrollee_name=auth_code.enrollee_name,
        cif_number=auth_code.cif_number,
        scheme_id=auth_code.scheme_id,
        visit_type_name=auth_code.visit_type_name,
        approved_amount=auth_code.approved_amount,
        claim_amount=claim_amount,
        provider_name=body.get("provider_name", ""),
        visit_date=body.get("visit_date", ""),
        reimbursement_reason=body.get("reimbursement_reason", ""),
        reason_for_visit=body.get("reason_for_visit", ""),
        remarks=body.get("remarks", ""),
        bank_name=body.get("bank_name", ""),
        account_number=body.get("account_number", ""),
        account_name=body.get("account_name", ""),
        documents_count=len(body.get("claim_documents", [])),
        claim_status="PENDING",
        prognosis_response=json.dumps(claims_result) if claims_result else None,
    )
    db.add(claim)
    db.commit()

    # Send confirmation email to member + claims team via Prognosis
    from app.services.email_service import send_claim_confirmation
    member_email = body.get("member_email", "")
    try:
        await send_claim_confirmation(
            member_email=member_email,
            enrollee_name=auth_code.enrollee_name,
            enrollee_id=auth_code.enrollee_id,
            pa_code=auth_code.code,
            visit_type=auth_code.visit_type_name,
            provider_name=body.get("provider_name", ""),
            visit_date=body.get("visit_date", ""),
            claim_amount=claim_amount,
            approved_amount=auth_code.approved_amount,
            bank_name=body.get("bank_name", ""),
            account_number=body.get("account_number", ""),
            account_name=body.get("account_name", ""),
            reason_for_visit=body.get("reason_for_visit", ""),
            remarks=body.get("remarks", ""),
            reimbursement_reason=body.get("reimbursement_reason", ""),
            batch_number=batch_number,
            prognosis_status=prognosis_status,
        )
    except Exception as e:
        log.error("Failed to send confirmation email: %s", e)

    return {
        "success": True,
        "message": "Reimbursement claim submitted successfully",
        "claim_id": str(claim.claim_id),
        "batch_number": batch_number,
        "code": auth_code.code,
        "enrollee_name": auth_code.enrollee_name,
        "visit_type_name": auth_code.visit_type_name,
        "approved_amount": auth_code.approved_amount,
        "claim_amount": claim_amount,
        "provider_name": body.get("provider_name", ""),
        "visit_date": body.get("visit_date", ""),
        "reason_for_visit": body.get("reason_for_visit", ""),
    }


@router.get("/reimbursement/banks")
async def list_banks():
    """Fetch list of Nigerian banks from Paystack."""
    from app.core.config import settings
    if not settings.PAYSTACK_SECRET_KEY:
        return {"success": False, "banks": []}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            resp = await client.get(
                "https://api.paystack.co/bank?country=nigeria&perPage=100",
                headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
            )
        if resp.status_code == 200:
            data = resp.json()
            banks = [{"name": b["name"], "code": b["code"]} for b in data.get("data", [])]
            return {"success": True, "banks": banks}
        return {"success": False, "banks": []}
    except Exception:
        return {"success": False, "banks": []}


@router.post("/reimbursement/validate-bank")
async def validate_bank_account(body: dict):
    """
    Validate bank account via Paystack Resolve Account API.
    GET https://api.paystack.co/bank/resolve?account_number=XXX&bank_code=XXX
    """
    import httpx as _httpx
    from app.core.config import settings

    account_number = body.get("account_number", "")
    bank_code = body.get("bank_code", "")

    if not account_number or not bank_code:
        return {"validated": False, "reason": "Account number and bank code required", "account_name": ""}

    if not settings.PAYSTACK_SECRET_KEY:
        return {"validated": False, "reason": "Paystack not configured", "account_name": ""}

    try:
        async with _httpx.AsyncClient(timeout=_httpx.Timeout(15.0)) as client:
            resp = await client.get(
                f"https://api.paystack.co/bank/resolve?account_number={account_number}&bank_code={bank_code}",
                headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
            )

        if resp.status_code == 200:
            data = resp.json()
            account_name = data.get("data", {}).get("account_name", "")
            return {
                "validated": True,
                "account_name": account_name,
                "message": "Account verified successfully",
            }
        else:
            error_msg = resp.json().get("message", "Could not resolve account")
            return {"validated": False, "reason": error_msg, "account_name": ""}
    except Exception as e:
        return {"validated": False, "reason": str(e), "account_name": ""}


# ── Claims Team endpoints ────────────────────────────────────

@router.post("/claims/login")
def claims_login(body: dict, db: Session = Depends(get_db)):
    """Claims team login — reuses Agent model with role check."""
    email = body.get("email", "")
    password = body.get("password", "")

    agent = db.query(Agent).filter(Agent.email == email).first()
    if not agent or not verify_password(password, agent.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not agent.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token(data={"sub": str(agent.agent_id), "role": "claims"})
    return {
        "access_token": token,
        "token_type": "bearer",
        "agent_id": str(agent.agent_id),
        "agent_name": agent.name,
        "role": "CLAIMS_OFFICER",
    }


def get_claims_officer(
    token: str = Depends(agent_oauth2),
    db: Session = Depends(get_db),
) -> Agent:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    agent_id = payload.get("sub")
    role = payload.get("role")
    if not agent_id or role != "claims":
        raise HTTPException(status_code=401, detail="Invalid token or insufficient role")
    agent = db.query(Agent).filter(Agent.agent_id == uuid.UUID(agent_id)).first()
    if not agent or not agent.is_active:
        raise HTTPException(status_code=401, detail="Agent not found or inactive")
    return agent


def _claim_to_dict(c: ReimbursementClaim) -> dict:
    return {
        "claim_id": str(c.claim_id),
        "pa_code": c.pa_code,
        "enrollee_id": c.enrollee_id,
        "enrollee_name": c.enrollee_name,
        "cif_number": c.cif_number,
        "scheme_id": c.scheme_id,
        "visit_type_name": c.visit_type_name,
        "approved_amount": c.approved_amount,
        "claim_amount": c.claim_amount,
        "provider_name": c.provider_name,
        "visit_date": c.visit_date,
        "reimbursement_reason": c.reimbursement_reason,
        "reason_for_visit": c.reason_for_visit,
        "remarks": c.remarks,
        "bank_name": c.bank_name,
        "account_number": c.account_number,
        "account_name": c.account_name,
        "documents_count": c.documents_count,
        "claim_status": c.claim_status,
        "reviewer_notes": c.reviewer_notes,
        "reviewed_by": c.reviewed_by,
        "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
        "created_at": c.created_at.isoformat(),
    }


@router.get("/claims/list")
def list_claims(
    status_filter: str = Query("ALL"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    officer: Agent = Depends(get_claims_officer),
):
    """List all reimbursement claims, optionally filtered by status."""
    q = db.query(ReimbursementClaim)
    if status_filter != "ALL":
        q = q.filter(ReimbursementClaim.claim_status == status_filter)
    claims = q.order_by(ReimbursementClaim.created_at.desc()).offset(skip).limit(limit).all()
    total = q.count()
    return {"total": total, "claims": [_claim_to_dict(c) for c in claims]}


@router.get("/claims/{claim_id}")
def get_claim_detail(
    claim_id: str,
    db: Session = Depends(get_db),
    officer: Agent = Depends(get_claims_officer),
):
    """Get full claim details."""
    claim = db.query(ReimbursementClaim).filter(
        ReimbursementClaim.claim_id == uuid.UUID(claim_id)
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return _claim_to_dict(claim)


@router.post("/claims/{claim_id}/review")
def review_claim(
    claim_id: str,
    body: dict,
    db: Session = Depends(get_db),
    officer: Agent = Depends(get_claims_officer),
):
    """Approve or reject a claim."""
    action = body.get("action", "").upper()  # APPROVED or REJECTED
    reviewer_notes = body.get("reviewer_notes", "")

    if action not in ("APPROVED", "REJECTED"):
        raise HTTPException(status_code=400, detail="action must be APPROVED or REJECTED")

    claim = db.query(ReimbursementClaim).filter(
        ReimbursementClaim.claim_id == uuid.UUID(claim_id)
    ).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.claim_status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Claim already {claim.claim_status}")

    claim.claim_status = action
    claim.reviewer_notes = reviewer_notes
    claim.reviewed_by = officer.name
    claim.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "success": True,
        "claim_id": str(claim.claim_id),
        "claim_status": claim.claim_status,
        "reviewed_by": claim.reviewed_by,
        "reviewer_notes": claim.reviewer_notes,
    }
