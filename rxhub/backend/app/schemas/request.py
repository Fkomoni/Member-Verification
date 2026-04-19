from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class RequestCreate(BaseModel):
    request_type: str = Field(..., pattern="^(PROFILE_UPDATE|MEDICATION_CHANGE|REFILL_ACTION)$")
    action: str = Field(..., pattern="^(ADD|REMOVE|MODIFY|REFILL|SUSPEND_REFILL|RESUME_REFILL)$")
    payload: dict
    comment: Optional[str] = None
    attachment_url: Optional[str] = None


class RequestOut(BaseModel):
    id: UUID
    member_id: str
    request_type: str
    action: str
    payload: dict
    comment: Optional[str] = None
    attachment_url: Optional[str] = None
    status: str
    admin_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RequestListOut(BaseModel):
    requests: list[RequestOut]
    total: int
    page: int
    page_size: int


class AdminRequestAction(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT|MODIFY)$")
    comment: Optional[str] = None
    modified_payload: Optional[dict] = None
