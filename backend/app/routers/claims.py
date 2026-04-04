"""
POST /claims-status – Get reimbursement claims status for a member by CIF number.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_provider
from app.models.models import Provider
from app.schemas.schemas import ClaimsStatusRequest, ClaimsStatusResponse
from app.services import prognosis_client

router = APIRouter(tags=["claims"])


@router.post("/claims-status", response_model=ClaimsStatusResponse)
async def claims_status(
    body: ClaimsStatusRequest,
    db: Session = Depends(get_db),
    provider: Provider = Depends(get_current_provider),
):
    result = await prognosis_client.get_claims_by_member(cifno=body.enrollee_id)

    claims = result.get("claims", [])

    return ClaimsStatusResponse(
        enrollee_id=body.enrollee_id,
        success=result.get("success", False),
        reason=result.get("reason"),
        claims=claims,
        total_claims=len(claims),
    )
