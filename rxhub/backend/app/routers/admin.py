from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.request import Request, RequestLog
from app.models.member import Member
from app.schemas.request import RequestOut, RequestListOut, AdminRequestAction
from app.services.sync_service import push_approved_request_to_pbm

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/requests", response_model=RequestListOut)
async def list_requests(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = Query(None, alias="status"),
    request_type: Optional[str] = None,
    member_id: Optional[str] = None,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all member requests with filters."""
    query = db.query(Request)

    if status_filter:
        query = query.filter(Request.status == status_filter.upper())
    if request_type:
        query = query.filter(Request.request_type == request_type.upper())
    if member_id:
        query = query.filter(Request.member_id == member_id)

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


@router.get("/requests/{request_id}", response_model=RequestOut)
async def get_request(
    request_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get a specific request with full details."""
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.post("/requests/{request_id}/approve")
async def approve_request(
    request_id: str,
    body: AdminRequestAction,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Approve a member request."""
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status not in ("PENDING", "REVIEWED"):
        raise HTTPException(status_code=400, detail=f"Cannot approve request with status {req.status}")

    before = {"status": req.status, "payload": req.payload}

    req.status = "APPROVED"
    req.admin_id = admin.id
    req.admin_comment = body.comment
    req.reviewed_at = datetime.now(timezone.utc)
    req.resolved_at = datetime.now(timezone.utc)

    log = RequestLog(
        request_id=req.id,
        actor_type="ADMIN",
        actor_id=str(admin.id),
        action="APPROVED",
        before_state=before,
        after_state={"status": "APPROVED", "admin_comment": body.comment},
        notes=f"Approved by {admin.full_name}",
    )
    db.add(log)
    db.commit()

    # Push to PBM async
    await push_approved_request_to_pbm(str(req.id), db)

    return {"message": "Request approved", "request_id": str(req.id)}


@router.post("/requests/{request_id}/reject")
async def reject_request(
    request_id: str,
    body: AdminRequestAction,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Reject a member request."""
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status not in ("PENDING", "REVIEWED"):
        raise HTTPException(status_code=400, detail=f"Cannot reject request with status {req.status}")

    before = {"status": req.status}

    req.status = "REJECTED"
    req.admin_id = admin.id
    req.admin_comment = body.comment
    req.reviewed_at = datetime.now(timezone.utc)
    req.resolved_at = datetime.now(timezone.utc)

    log = RequestLog(
        request_id=req.id,
        actor_type="ADMIN",
        actor_id=str(admin.id),
        action="REJECTED",
        before_state=before,
        after_state={"status": "REJECTED", "admin_comment": body.comment},
        notes=f"Rejected by {admin.full_name}",
    )
    db.add(log)
    db.commit()

    return {"message": "Request rejected", "request_id": str(req.id)}


@router.post("/requests/{request_id}/modify")
async def modify_request(
    request_id: str,
    body: AdminRequestAction,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Modify a request payload before approval."""
    req = db.query(Request).filter(Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if req.status not in ("PENDING", "REVIEWED"):
        raise HTTPException(status_code=400, detail=f"Cannot modify request with status {req.status}")

    if not body.modified_payload:
        raise HTTPException(status_code=400, detail="modified_payload required for MODIFY action")

    before = {"status": req.status, "payload": req.payload}

    req.status = "MODIFIED"
    req.payload = body.modified_payload
    req.admin_id = admin.id
    req.admin_comment = body.comment
    req.reviewed_at = datetime.now(timezone.utc)

    log = RequestLog(
        request_id=req.id,
        actor_type="ADMIN",
        actor_id=str(admin.id),
        action="MODIFIED",
        before_state=before,
        after_state={"status": "MODIFIED", "payload": body.modified_payload, "admin_comment": body.comment},
        notes=f"Modified by {admin.full_name}",
    )
    db.add(log)
    db.commit()

    return {"message": "Request modified", "request_id": str(req.id)}


@router.get("/audit-logs")
async def get_audit_logs(
    request_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get audit logs with filters."""
    query = db.query(RequestLog)
    if request_id:
        query = query.filter(RequestLog.request_id == request_id)
    if actor_id:
        query = query.filter(RequestLog.actor_id == actor_id)

    total = query.count()
    logs = (
        query.order_by(RequestLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {"logs": logs, "total": total, "page": page, "page_size": page_size}


@router.get("/analytics")
async def get_analytics(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """User analytics: active members, request counts, etc."""
    total_members = db.query(Member).filter(Member.status == "ACTIVE").count()

    from sqlalchemy import func, distinct
    active_members = (
        db.query(func.count(distinct(Request.member_id)))
        .filter(Request.created_at >= func.now() - func.cast("30 days", func.text("interval")))
        .scalar()
    ) or 0

    request_stats = {}
    for s in ["PENDING", "APPROVED", "REJECTED", "MODIFIED"]:
        request_stats[s.lower()] = db.query(Request).filter(Request.status == s).count()

    return {
        "total_active_members": total_members,
        "members_with_activity_30d": active_members,
        "request_stats": request_stats,
    }
