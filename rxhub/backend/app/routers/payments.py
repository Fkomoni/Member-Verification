from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_member
from app.models.member import Member
from app.models.payment import Payment
from app.schemas.payment import PaymentInitiate, PaymentVerify, PaymentOut
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/initiate", response_model=dict)
async def initiate_payment(
    body: PaymentInitiate,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Initiate a payment via Paystack."""
    payment = Payment(
        member_id=member.member_id,
        medication_id=body.medication_id,
        amount=body.amount,
        payment_type=body.payment_type,
        metadata=body.metadata or {},
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    result = await payment_service.initialize_payment(payment, member.email, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/verify", response_model=dict)
async def verify_payment(
    body: PaymentVerify,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Verify a payment with Paystack."""
    result = await payment_service.verify_payment(body.gateway_ref, db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/history", response_model=list[PaymentOut])
async def payment_history(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Get member payment history."""
    payments = (
        db.query(Payment)
        .filter(Payment.member_id == member.member_id)
        .order_by(Payment.created_at.desc())
        .limit(50)
        .all()
    )
    return payments
