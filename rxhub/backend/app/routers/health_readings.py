import csv
import io
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_member
from app.models.member import Member
from app.models.health_reading import HealthReading
from app.schemas.health_reading import HealthReadingCreate, HealthReadingOut

router = APIRouter(prefix="/health-readings", tags=["Health Readings"])


# ── Normal ranges for trend classification ────────────────────
NORMAL_RANGES = {
    "BLOOD_PRESSURE": {"systolic": (90, 120), "diastolic": (60, 80)},
    "BLOOD_GLUCOSE": {"fasting": (70, 100), "random": (70, 140), "post_meal": (70, 140)},
    "CHOLESTEROL": {"total": (0, 200), "hdl": (40, 999), "ldl": (0, 100), "triglycerides": (0, 150)},
}


def _classify_bp(systolic, diastolic):
    if systolic < 120 and diastolic < 80:
        return "NORMAL"
    if systolic < 130 and diastolic < 80:
        return "ELEVATED"
    if systolic < 140 or diastolic < 90:
        return "HIGH (Stage 1)"
    return "HIGH (Stage 2)"


def _classify_glucose(level, context):
    if context == "FASTING":
        if level < 100: return "NORMAL"
        if level < 126: return "PRE-DIABETIC"
        return "DIABETIC RANGE"
    else:
        if level < 140: return "NORMAL"
        if level < 200: return "PRE-DIABETIC"
        return "DIABETIC RANGE"


def _classify_cholesterol(total):
    if total < 200: return "DESIRABLE"
    if total < 240: return "BORDERLINE HIGH"
    return "HIGH"


def _compute_trend(readings, value_fn):
    """Compare last 3 readings to determine trend direction."""
    if len(readings) < 2:
        return "INSUFFICIENT_DATA"

    values = [value_fn(r) for r in readings[:5] if value_fn(r) is not None]
    if len(values) < 2:
        return "INSUFFICIENT_DATA"

    # Compare most recent vs average of older readings
    latest = values[0]
    older_avg = sum(values[1:]) / len(values[1:])
    diff_pct = ((latest - older_avg) / older_avg * 100) if older_avg else 0

    if abs(diff_pct) < 3:
        return "STABLE"
    elif diff_pct < 0:
        return "IMPROVING"
    else:
        return "WORSENING"


# ── CRUD ──────────────────────────────────────────────────────

@router.post("", response_model=HealthReadingOut, status_code=201)
async def create_reading(
    body: HealthReadingCreate,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Log a new health reading."""
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
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 50,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """Get health reading history with optional date range filter."""
    query = db.query(HealthReading).filter(HealthReading.member_id == member.member_id)
    if reading_type:
        query = query.filter(HealthReading.reading_type == reading_type.upper())
    if date_from:
        query = query.filter(HealthReading.recorded_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(HealthReading.recorded_at <= datetime.combine(date_to, datetime.max.time()))

    return query.order_by(HealthReading.recorded_at.desc()).limit(limit).all()


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


# ── TREND ANALYSIS ────────────────────────────────────────────

@router.get("/trends")
async def get_trends(
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """
    Analyze health trends per reading type.
    Compares recent readings to determine if member is improving, stable, or worsening.
    """
    trends = {}

    for rtype in ["BLOOD_PRESSURE", "BLOOD_GLUCOSE", "CHOLESTEROL"]:
        readings = (
            db.query(HealthReading)
            .filter(HealthReading.member_id == member.member_id, HealthReading.reading_type == rtype)
            .order_by(HealthReading.recorded_at.desc())
            .limit(10)
            .all()
        )

        if not readings:
            trends[rtype] = {"trend": "NO_DATA", "classification": None, "reading_count": 0, "latest": None, "previous": None, "change": None}
            continue

        latest = readings[0]
        previous = readings[1] if len(readings) > 1 else None

        if rtype == "BLOOD_PRESSURE":
            trend = _compute_trend(readings, lambda r: float(r.systolic) if r.systolic else None)
            classification = _classify_bp(float(latest.systolic), float(latest.diastolic))
            latest_val = f"{latest.systolic}/{latest.diastolic}"
            prev_val = f"{previous.systolic}/{previous.diastolic}" if previous else None
            change = None
            if previous and latest.systolic and previous.systolic:
                sys_diff = float(latest.systolic) - float(previous.systolic)
                dia_diff = float(latest.diastolic) - float(previous.diastolic)
                change = f"{'+'if sys_diff>=0 else ''}{sys_diff:.0f}/{'+'if dia_diff>=0 else ''}{dia_diff:.0f} mmHg"

        elif rtype == "BLOOD_GLUCOSE":
            trend = _compute_trend(readings, lambda r: float(r.glucose_level) if r.glucose_level else None)
            classification = _classify_glucose(float(latest.glucose_level), latest.glucose_context or "RANDOM")
            latest_val = f"{latest.glucose_level} mg/dL"
            prev_val = f"{previous.glucose_level} mg/dL" if previous else None
            change = None
            if previous and latest.glucose_level and previous.glucose_level:
                diff = float(latest.glucose_level) - float(previous.glucose_level)
                change = f"{'+'if diff>=0 else ''}{diff:.0f} mg/dL"

        elif rtype == "CHOLESTEROL":
            trend = _compute_trend(readings, lambda r: float(r.total_cholesterol) if r.total_cholesterol else None)
            classification = _classify_cholesterol(float(latest.total_cholesterol))
            latest_val = f"{latest.total_cholesterol} mg/dL"
            prev_val = f"{previous.total_cholesterol} mg/dL" if previous else None
            change = None
            if previous and latest.total_cholesterol and previous.total_cholesterol:
                diff = float(latest.total_cholesterol) - float(previous.total_cholesterol)
                change = f"{'+'if diff>=0 else ''}{diff:.0f} mg/dL"

        trends[rtype] = {
            "trend": trend,
            "classification": classification,
            "reading_count": len(readings),
            "latest": latest_val,
            "previous": prev_val,
            "change": change,
            "latest_date": latest.recorded_at.isoformat() if latest.recorded_at else None,
            "previous_date": previous.recorded_at.isoformat() if previous and previous.recorded_at else None,
        }

    return trends


# ── CSV DOWNLOAD ──────────────────────────────────────────────

@router.get("/download")
async def download_readings(
    reading_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    member: Member = Depends(get_current_member),
    db: Session = Depends(get_db),
):
    """
    Download health readings as CSV for a given date range.
    Includes date, type, all values, classification, and notes.
    """
    query = db.query(HealthReading).filter(HealthReading.member_id == member.member_id)
    if reading_type:
        query = query.filter(HealthReading.reading_type == reading_type.upper())
    if date_from:
        query = query.filter(HealthReading.recorded_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(HealthReading.recorded_at <= datetime.combine(date_to, datetime.max.time()))

    readings = query.order_by(HealthReading.recorded_at.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Date", "Time", "Type", "Reading", "Classification",
        "Systolic", "Diastolic",
        "Glucose Level", "Glucose Context",
        "Total Cholesterol", "HDL", "LDL", "Triglycerides",
        "Notes",
    ])

    for r in readings:
        dt = r.recorded_at
        date_str = dt.strftime("%Y-%m-%d") if dt else ""
        time_str = dt.strftime("%H:%M") if dt else ""

        if r.reading_type == "BLOOD_PRESSURE":
            reading_str = f"{r.systolic}/{r.diastolic} mmHg"
            classification = _classify_bp(float(r.systolic), float(r.diastolic))
        elif r.reading_type == "BLOOD_GLUCOSE":
            reading_str = f"{r.glucose_level} mg/dL"
            classification = _classify_glucose(float(r.glucose_level), r.glucose_context or "RANDOM")
        elif r.reading_type == "CHOLESTEROL":
            reading_str = f"{r.total_cholesterol} mg/dL"
            classification = _classify_cholesterol(float(r.total_cholesterol))
        else:
            reading_str = ""
            classification = ""

        writer.writerow([
            date_str, time_str,
            r.reading_type.replace("_", " "),
            reading_str, classification,
            r.systolic or "", r.diastolic or "",
            r.glucose_level or "", r.glucose_context or "",
            r.total_cholesterol or "", r.hdl or "", r.ldl or "", r.triglycerides or "",
            r.notes or "",
        ])

    output.seek(0)

    filename = f"health_readings_{member.member_id.replace('/', '-')}_{date.today().isoformat()}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
