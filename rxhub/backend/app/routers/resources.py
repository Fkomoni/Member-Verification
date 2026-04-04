from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_member, get_current_admin
from app.models.member import Member
from app.models.admin import Admin
from app.models.resource import Resource
from app.schemas.resource import ResourceOut, ResourceCreate, ResourceUpdate

router = APIRouter(prefix="/resources", tags=["Resources"])


@router.get("", response_model=list[ResourceOut])
async def list_resources(
    diagnosis: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    """Public: list published resources, filterable by diagnosis or category."""
    query = db.query(Resource).filter(Resource.is_published.is_(True))

    if diagnosis:
        query = query.filter(Resource.diagnosis_tags.any(diagnosis))
    if category:
        query = query.filter(Resource.category == category.upper())

    resources = (
        query.order_by(Resource.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return resources


@router.get("/{resource_id}", response_model=ResourceOut)
async def get_resource(resource_id: str, db: Session = Depends(get_db)):
    """Get a single resource."""
    resource = db.query(Resource).filter(Resource.id == resource_id, Resource.is_published.is_(True)).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


# --- Admin endpoints ---

@router.post("/admin", response_model=ResourceOut)
async def create_resource(
    body: ResourceCreate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin: create a new resource."""
    resource = Resource(
        title=body.title,
        body=body.body,
        category=body.category,
        diagnosis_tags=body.diagnosis_tags,
        thumbnail_url=body.thumbnail_url,
        is_published=body.is_published,
        published_at=datetime.now(timezone.utc) if body.is_published else None,
        author_id=admin.id,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.put("/admin/{resource_id}", response_model=ResourceOut)
async def update_resource(
    resource_id: str,
    body: ResourceUpdate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin: update a resource."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)

    if body.is_published and not resource.published_at:
        resource.published_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/admin/{resource_id}")
async def delete_resource(
    resource_id: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin: delete a resource."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    db.delete(resource)
    db.commit()
    return {"message": "Resource deleted"}
