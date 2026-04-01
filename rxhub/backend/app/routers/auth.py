from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.models.member import Member
from app.models.admin import Admin
from app.schemas.auth import (
    LoginRequest, LoginResponse,
    SendOTPRequest, SendOTPResponse,
    VerifyOTPRequest,
    AdminLoginRequest, AdminLoginResponse,
)
from app.services.pbm_client import prognosis_client
from app.services.otp_service import otp_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _upsert_member_from_prognosis(enrollee: dict, db: Session) -> Member:
    """Create or update local member record from Prognosis enrollee data."""
    # Prognosis field mapping (handle multiple possible field name formats)
    def get(field, *alts):
        for f in [field] + list(alts):
            val = enrollee.get(f) or enrollee.get(f.lower()) or enrollee.get(f[0].upper() + f[1:])
            if val:
                return val
        return None

    member_id = (
        get("enrolleeID", "EnrolleeID", "enrollee_id", "MemberID", "memberId", "member_id") or
        get("enrolleeid", "ENROLLEEID") or ""
    )

    if not member_id:
        return None

    member = db.query(Member).filter(Member.member_id == str(member_id)).first()
    if not member:
        member = Member(member_id=str(member_id))
        db.add(member)

    # Map Prognosis fields to our member model
    member.first_name = get("firstName", "FirstName", "first_name", "Firstname") or member.first_name or "Member"
    member.last_name = get("lastName", "LastName", "last_name", "Lastname", "surname", "Surname") or member.last_name or ""
    member.email = get("email", "Email", "emailAddress", "EmailAddress") or member.email
    member.phone = get("phone", "Phone", "phoneNumber", "PhoneNumber", "mobileNumber", "MobileNumber", "telephone", "Telephone") or member.phone or ""
    member.gender = get("gender", "Gender", "sex", "Sex") or member.gender
    member.diagnosis = get("diagnosis", "Diagnosis", "primaryDiagnosis", "PrimaryDiagnosis") or member.diagnosis
    member.plan_type = get("planType", "PlanType", "plan_type", "planCode", "PlanCode") or member.plan_type
    member.plan_name = get("planName", "PlanName", "plan_name", "plan", "Plan") or member.plan_name
    member.employer = get("employer", "Employer", "company", "Company", "organizationName", "OrganizationName") or member.employer
    member.status = "ACTIVE"
    member.pbm_synced_at = datetime.now(timezone.utc)

    # Try to parse date_of_birth
    dob = get("dateOfBirth", "DateOfBirth", "date_of_birth", "dob", "DOB")
    if dob and isinstance(dob, str):
        try:
            from dateutil import parser as date_parser
            member.date_of_birth = date_parser.parse(dob).date()
        except Exception:
            pass

    db.commit()
    db.refresh(member)
    return member


def _normalize_phone(phone: str) -> str:
    """Normalize Nigerian phone to 0XXXXXXXXXX."""
    if not phone:
        return ""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+234"):
        phone = "0" + phone[4:]
    elif phone.startswith("234") and len(phone) > 10:
        phone = "0" + phone[3:]
    return phone


def _local_validate(member_id: str, phone: str, db: Session) -> Member:
    """Validate against local DB when Prognosis API is unreachable."""
    member = db.query(Member).filter(Member.member_id == member_id).first()
    if not member:
        return None
    if _normalize_phone(member.phone) == _normalize_phone(phone):
        return member
    return None


@router.post("/login", response_model=LoginResponse)
async def member_login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Primary login: validate member_id + phone against Prognosis API.
    Falls back to local DB validation if Prognosis is unreachable.
    """
    member = None
    auth_method = "API"

    # Try Prognosis API first
    result = await prognosis_client.validate_member(req.member_id, req.phone, db=db)

    if result.get("valid"):
        # Prognosis validated — upsert member from API data
        member = _upsert_member_from_prognosis(result, db)
    elif "Connection error" in str(result.get("error", "")) or "Timeout" in str(result.get("error", "")):
        # Prognosis unreachable — fall back to local DB
        import logging
        logging.getLogger(__name__).warning("Prognosis API unreachable, falling back to local validation")
        member = _local_validate(req.member_id, req.phone, db)
        auth_method = "LOCAL"
    else:
        # Prognosis responded but validation failed (wrong phone, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.get("error", "Validation failed. Please check your Member ID and phone number, or use OTP login."),
        )

    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Validation failed. Please check your Member ID and phone number.",
        )

    token = create_access_token(
        {"sub": member.member_id, "type": "member", "auth_method": auth_method}
    )

    return LoginResponse(
        access_token=token,
        auth_method=auth_method,
        member_id=member.member_id,
        member_name=f"{member.first_name} {member.last_name}".strip(),
    )


@router.post("/send-otp", response_model=SendOTPResponse)
async def send_otp(req: SendOTPRequest, db: Session = Depends(get_db)):
    """
    Fallback OTP: fetch registered phone from Prognosis (or local DB), send OTP to it.
    """
    phone = None

    # Try Prognosis first
    enrollee = await prognosis_client.get_member(req.member_id, db=db)
    if "error" not in enrollee:
        phone = (
            enrollee.get("phone") or enrollee.get("Phone") or
            enrollee.get("phoneNumber") or enrollee.get("PhoneNumber") or
            enrollee.get("mobileNumber") or enrollee.get("MobileNumber") or
            enrollee.get("telephone") or enrollee.get("Telephone") or ""
        )

    # Fallback to local DB
    if not phone:
        local_member = db.query(Member).filter(Member.member_id == req.member_id).first()
        if local_member:
            phone = local_member.phone

    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found. Please verify your Member ID.",
        )

    result = await otp_service.send_otp(req.member_id, phone, db)
    return SendOTPResponse(**result)


@router.post("/verify-otp", response_model=LoginResponse)
async def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP and create session."""
    valid = await otp_service.verify(req.member_id, req.otp, db)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP. Please try again.",
        )

    # Fetch enrollee data and upsert member
    enrollee = await prognosis_client.get_member(req.member_id, db=db)
    member = _upsert_member_from_prognosis(enrollee, db) if "error" not in enrollee else None

    if not member:
        member = db.query(Member).filter(Member.member_id == req.member_id).first()

    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    token = create_access_token(
        {"sub": member.member_id, "type": "member", "auth_method": "OTP"}
    )

    return LoginResponse(
        access_token=token,
        auth_method="OTP",
        member_id=member.member_id,
        member_name=f"{member.first_name} {member.last_name}".strip(),
    )


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(req: AdminLoginRequest, db: Session = Depends(get_db)):
    """Admin portal login."""
    admin = db.query(Admin).filter(Admin.email == req.email, Admin.is_active.is_(True)).first()
    if not admin or not verify_password(req.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    admin.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        {"sub": str(admin.id), "type": "admin", "role": admin.role},
        expires_minutes=settings.JWT_ADMIN_TOKEN_EXPIRE_MINUTES,
    )

    return AdminLoginResponse(
        access_token=token,
        admin_name=admin.full_name,
        role=admin.role,
    )
