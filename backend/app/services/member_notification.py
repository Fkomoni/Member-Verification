"""
Member Notification — sends email via Prognosis SendEmailAlert API.

POST /api/EnrolleeProfile/SendEmailAlert
"""

import logging

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.medication import MedicationAuditLog, MedicationRequest, MedicationRequestItem
from app.services.prognosis_client import _get_prognosis_token

logger = logging.getLogger(__name__)


def _build_email_html(
    member_name: str,
    member_phone: str,
    delivery_address: str,
    facility_name: str,
    reference: str,
    diagnosis: str,
    medications: list[dict],
    pharmacy_name: str,
    tracking_code: str,
    tracking_link: str,
) -> str:
    med_rows = ""
    for i, m in enumerate(medications, 1):
        med_rows += f"""<tr>
            <td style="padding:10px;border:1px solid #e0e0e0">{i}</td>
            <td style="padding:10px;border:1px solid #e0e0e0">{m['name']}</td>
            <td style="padding:10px;border:1px solid #e0e0e0">{m.get('strength','')}</td>
            <td style="padding:10px;border:1px solid #e0e0e0">{m.get('dose','')}</td>
            <td style="padding:10px;border:1px solid #e0e0e0">{m.get('frequency','')}</td>
            <td style="padding:10px;border:1px solid #e0e0e0">{m.get('duration','')}</td>
        </tr>"""

    track_btn = ""
    if tracking_link:
        track_btn = f'<p style="margin-top:20px"><a href="{tracking_link}" style="display:inline-block;background:#C61531;color:#fff;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:14px">Track Your Order</a></p>'

    return f"""
<div style="font-family:Arial,sans-serif;max-width:650px;margin:0 auto;background:#fff;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden">
    <div style="background:#C61531;padding:20px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:22px">LEADWAY Health</h1>
        <p style="color:#FFE0E0;margin:5px 0 0;font-size:13px">Medication Fulfilment Notification</p>
    </div>
    <div style="padding:25px">
        <p style="font-size:15px">Dear <strong>{member_name}</strong>,</p>
        <p style="color:#555;line-height:1.6"><strong>{facility_name}</strong> has submitted a medication request on your behalf through the Leadway Health portal. All prescribed medications are <strong>acute</strong> and have been logged for fulfilment by our partner pharmacy.</p>

        <div style="background:#F8F9FA;border-radius:8px;padding:15px;margin:20px 0;border-left:4px solid #C61531">
            <table style="width:100%;font-size:14px">
                <tr><td style="padding:4px 0;color:#777;width:120px">Reference:</td><td style="font-weight:bold">{reference}</td></tr>
                <tr><td style="padding:4px 0;color:#777">Diagnosis:</td><td>{diagnosis}</td></tr>
                <tr><td style="padding:4px 0;color:#777">Phone:</td><td>{member_phone}</td></tr>
                <tr><td style="padding:4px 0;color:#777">Delivery Address:</td><td>{delivery_address}</td></tr>
            </table>
        </div>

        <h3 style="color:#C61531;border-bottom:2px solid #C61531;padding-bottom:8px;margin-top:25px">Medications Prescribed</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px;margin-top:10px">
            <tr style="background:#263626;color:#fff">
                <th style="padding:10px;text-align:left">#</th>
                <th style="padding:10px;text-align:left">Medication</th>
                <th style="padding:10px;text-align:left">Strength</th>
                <th style="padding:10px;text-align:left">Dose</th>
                <th style="padding:10px;text-align:left">Frequency</th>
                <th style="padding:10px;text-align:left">Duration</th>
            </tr>
            {med_rows}
        </table>

        <h3 style="color:#C61531;margin-top:25px">Pharmacy Assigned</h3>
        <div style="background:#E8F8EE;border-radius:8px;padding:15px;border:1px solid #B5E8C9">
            <p style="margin:0 0 8px;font-size:15px"><strong>{pharmacy_name}</strong></p>
            <p style="margin:0 0 8px;font-size:20px;font-weight:bold;color:#0A7C3E">Tracking Code: {tracking_code}</p>
        </div>

        <h3 style="color:#C61531;margin-top:25px">What Happens Next?</h3>
        <ol style="line-height:2;color:#555;font-size:14px">
            <li>The pharmacy will confirm availability of your medications</li>
            <li>Once confirmed, you will receive a <strong>Pickup Code</strong> via SMS</li>
            <li>Present the Pickup Code at the pharmacy to collect your medications</li>
        </ol>

        {track_btn}

        <p style="color:#999;font-size:11px;margin-top:30px;border-top:1px solid #eee;padding-top:15px">
            This is an automated notification from Leadway Health Services.
            If you have questions, contact your healthcare provider or call Leadway Health support.
        </p>
    </div>
    <div style="background:#263626;padding:15px;text-align:center;font-size:12px;color:#B8B8C8">
        Leadway Health Services &mdash; For health, wealth &amp; more...
    </div>
</div>"""


async def send_member_email(
    request_id: str,
    db: Session,
    pharmacy_name: str = "",
    tracking_code: str = "",
    tracking_link: str = "",
):
    """Send member notification via Prognosis SendEmailAlert API."""
    req = db.query(MedicationRequest).filter(MedicationRequest.request_id == request_id).first()
    if not req or not req.member_email:
        logger.info("No email for member — skipping notification")
        return

    items = db.query(MedicationRequestItem).filter(MedicationRequestItem.request_id == request_id).all()
    medications = [
        {
            "name": item.drug_name,
            "strength": item.strength or "",
            "dose": item.dosage_instruction or "",
            "frequency": item.route or "",
            "duration": item.duration or "",
        }
        for item in items
    ]

    html = _build_email_html(
        member_name=req.enrollee_name,
        member_phone=req.member_phone or "",
        delivery_address=req.delivery_address or "",
        facility_name=req.facility_name,
        reference=req.reference_number,
        diagnosis=req.diagnosis,
        medications=medications,
        pharmacy_name=pharmacy_name,
        tracking_code=tracking_code,
        tracking_link=tracking_link,
    )

    # Send via Prognosis API
    base_url = settings.PROGNOSIS_BASE_URL.rstrip("/")
    token = await _get_prognosis_token()
    if not token:
        logger.error("Cannot send email — no Prognosis token")
        return

    email_payload = {
        "EmailAddress": req.member_email,
        "CC": "",
        "BCC": "",
        "Subject": f"Your Medication Request {req.reference_number} - Leadway Health",
        "MessageBody": html,
        "Attachments": None,
        "Category": "MedicationFulfilment",
        "UserId": 0,
        "ProviderId": 0,
        "ServiceId": 0,
        "Reference": req.reference_number,
        "TransactionType": "AcuteFulfilment",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), verify=False) as client:
            resp = await client.post(
                f"{base_url}/api/EnrolleeProfile/SendEmailAlert",
                json=email_payload,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
        logger.info("Email API response: %d %s", resp.status_code, resp.text[:200])

        db.add(MedicationAuditLog(
            event_type="member_email_sent",
            request_id=request_id,
            detail=f"Email sent to {req.member_email}. Status: {resp.status_code}",
        ))
        db.flush()

    except Exception as e:
        logger.error("Email send failed: %s", e)
