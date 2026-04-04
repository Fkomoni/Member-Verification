from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class ResourceOut(BaseModel):
    id: UUID
    title: str
    body: str
    category: str
    diagnosis_tags: list[str]
    thumbnail_url: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResourceCreate(BaseModel):
    title: str
    body: str
    category: str
    diagnosis_tags: list[str] = []
    thumbnail_url: Optional[str] = None
    is_published: bool = False


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    diagnosis_tags: Optional[list[str]] = None
    thumbnail_url: Optional[str] = None
    is_published: Optional[bool] = None
