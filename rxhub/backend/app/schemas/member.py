from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class MemberProfile(BaseModel):
    id: UUID
    member_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    plan_type: Optional[str] = None
    plan_name: Optional[str] = None
    employer: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}


class MemberDashboard(BaseModel):
    profile: MemberProfile
    medications_count: int
    pending_requests: int
    unread_notifications: int
    alerts: list[dict]
