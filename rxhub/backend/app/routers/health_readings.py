from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_member
from app.models.member import Member
from app.models.health_reading import HealthReading
from app.schemas.health_reading import HealthReadingCreate, HealthReadingOut

router = APIRouter(prefix="/health-readings", tags=["Health Readings"])


@router.post("", response_model=HealthReadingOut, status_code=201)
async def create_reading(
    body: HealthReadingCreate,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Log a new health reading (BP, Blood Glucose, or Cholesterol)."""
    # Validate required fields per type
    if body.reading_type == "BLOOD_PRESSURE":
        if not body.systolic or not body.diastolic:
            raise HTTPException(status_code=400, detail="Systolic and diastolic values are required for blood pressure")

    elif body.reading_type == "BLOOD_GLUCOSE":
        if not body.glucose_level:
            raise HTTPException(status_code=400, detail="Glucose level is required")

    elif body.reading_type == "CHOLESTEROL":
        if not body.total_cholesterol:
            raise HTTPException(status_code=400, detail="Total cholesterol is required")

    reading = HealthReading(
        member_id=member.member_id,
        reading_type=body.reading_type,
        systolic=body.systolic,
        diastolic=body.diastolic,
        glucose_level=body.glucose_level,
        glucose_context=body.glucose_context,
        total_cholesterol=body.total_cholesterol,
        hdl=body.hdl,
        ldl=body.ldl,
        triglycerides=body.triglycerides,
        notes=body.notes,
        recorded_at=body.recorded_at or datetime.now(timezone.utc),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("", response_model=list[HealthReadingOut])
async def list_readings(
    reading_type: Optional[str] = None,
    limit: int = 30,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Get health reading history, optionally filtered by type."""
    query = db.query(HealthReading).filter(HealthReading.member_id == member.member_id)
    if reading_type:
        query = query.filter(HealthReading.reading_type == reading_type.upper())

    readings = query.order_by(HealthReading.recorded_at.desc()).limit(limit).all()
    return readings


@router.get("/latest")
async def latest_readings(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Get the most recent reading for each type."""
    result = {}
    for rtype in ["BLOOD_PRESSURE", "BLOOD_GLUCOSE", "CHOLESTEROL"]:
        reading = (
            db.query(HealthReading)
            .filter(HealthReading.member_id == member.member_id, HealthReading.reading_type == rtype)
            .order_by(HealthReading.recorded_at.desc())
            .first()
        )
        if reading:
            result[rtype] = HealthReadingOut.model_validate(reading).model_dump(mode="json")
        else:
            result[rtype] = None

    return result


@router.delete("/{reading_id}")
async def delete_reading(
    reading_id: str,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Delete a health reading."""
    reading = (
        db.query(HealthReading)
        .filter(HealthReading.id == reading_id, HealthReading.member_id == member.member_id)
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    db.delete(reading)
    db.commit()
    return {"status": "deleted"}
