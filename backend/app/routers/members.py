"""POST /verify-member – Look up member and check biometric status."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_provider
from backend.app.models.models import Member, Provider
from backend.app.schemas.schemas import MemberLookup, MemberResponse

router = APIRouter(tags=["members"])


@router.post("/verify-member", response_model=MemberResponse)
def verify_member(
    body: MemberLookup,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    member = db.query(Member).filter(Member.enrollee_id == body.enrollee_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member with enrollee ID '{body.enrollee_id}' not found",
        )
    return member
