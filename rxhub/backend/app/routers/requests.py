from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_member
from app.models.member import Member
from app.models.request import Request, RequestLog
from app.schemas.request import RequestCreate, RequestOut, RequestListOut
from app.services.s3_service import s3_service

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
async def create_request(
    request_type: str = Form(...),
    action: str = Form(...),
    payload: str = Form(...),  # JSON string
    comment: Optional[str] = Form(None),
    attachment: Optional[UploadFile] = File(None),
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Create a new change request. Attachment required for MEDICATION_CHANGE + ADD."""
    import json

    try:
        payload_dict = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in payload")

    # Validate: new medication requires prescription upload
    if request_type == "MEDICATION_CHANGE" and action == "ADD":
        if not attachment:
            raise HTTPException(
                status_code=400,
                detail="Prescription upload required for new medication requests",
            )
        if not comment:
            raise HTTPException(
                status_code=400,
                detail="Comment required for new medication requests",
            )

    attachment_url = None
    if attachment:
        try:
            attachment_url = await s3_service.upload_file(attachment, folder="prescriptions")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    req = Request(
        member_id=member.member_id,
        request_type=request_type,
        action=action,
        payload=payload_dict,
        comment=comment,
        attachment_url=attachment_url,
    )
    db.add(req)
    db.flush()

    # Audit log
    log = RequestLog(
        request_id=req.id,
        actor_type="MEMBER",
        actor_id=member.member_id,
        action="CREATED",
        after_state={"status": "PENDING", "payload": payload_dict},
    )
    db.add(log)
    db.commit()
    db.refresh(req)

    return req


@router.get("/my", response_model=RequestListOut)
async def get_my_requests(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Get current member's requests with pagination."""
    query = db.query(Request).filter(Request.member_id == member.member_id)

    if status_filter:
        query = query.filter(Request.status == status_filter.upper())

    total = query.count()
    requests = (
        query.order_by(Request.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return RequestListOut(
        requests=[RequestOut.model_validate(r) for r in requests],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{request_id}", response_model=RequestOut)
async def get_request(
    request_id: str,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Get a specific request."""
    req = (
        db.query(Request)
        .filter(Request.id == request_id, Request.member_id == member.member_id)
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req
