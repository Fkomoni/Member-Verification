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
from app.services.pbm_client import pbm_client
from app.services.otp_service import otp_service
from app.services.sync_service import sync_member_from_pbm, sync_medications_from_pbm

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def member_login(req: LoginRequest, db: Session = Depends(get_db)):
    """Primary login: validate member_id + phone against PBM API."""
    result = await pbm_client.validate_member(req.member_id, req.phone, db=db)

    if "error" in result or not result.get("valid", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Validation failed. Please check your Member ID and phone number, or use OTP login.",
        )

    # Sync member data from PBM on login
    await sync_member_from_pbm(req.member_id, db)
    await sync_medications_from_pbm(req.member_id, db)

    member = db.query(Member).filter(Member.member_id == req.member_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found after sync")

    token = create_access_token(
        {"sub": member.member_id, "type": "member", "auth_method": "API"}
    )

    return LoginResponse(
        access_token=token,
        auth_method="API",
        member_id=member.member_id,
        member_name=f"{member.first_name} {member.last_name}",
    )


@router.post("/send-otp", response_model=SendOTPResponse)
async def send_otp(req: SendOTPRequest, db: Session = Depends(get_db)):
    """Fallback: fetch registered phone from PBM, send OTP."""
    pbm_data = await pbm_client.get_member(req.member_id, db=db)
    if "error" in pbm_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in PBM system")

    phone = pbm_data.get("phone")
    if not phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No phone number on file")

    result = await otp_service.send_otp(req.member_id, phone, db)
    return SendOTPResponse(**result)


@router.post("/verify-otp", response_model=LoginResponse)
async def verify_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP and create session."""
    valid = await otp_service.verify(req.member_id, req.otp, db)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP")

    await sync_member_from_pbm(req.member_id, db)
    await sync_medications_from_pbm(req.member_id, db)

    member = db.query(Member).filter(Member.member_id == req.member_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found after sync")

    token = create_access_token(
        {"sub": member.member_id, "type": "member", "auth_method": "OTP"}
    )

    return LoginResponse(
        access_token=token,
        auth_method="OTP",
        member_id=member.member_id,
        member_name=f"{member.first_name} {member.last_name}",
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
