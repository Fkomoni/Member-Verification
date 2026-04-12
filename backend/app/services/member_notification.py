"""
Member Notification Service — sends email notifications to members.

Sends automatic email when medication request is dispatched:
- Acute (WellaHealth): pharmacy details, tracking code, pickup instructions
- Chronic (WhatsApp): confirmation that request was sent to Leadway team
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app.models.medication import MedicationAuditLog, MedicationRequest, MedicationRequestItem

logger = logging.getLogger(__name__)


def _build_acute_email(
    member_name: str,
    member_email: str,
    facility_name: str,
    reference: str,
    diagnosis: str,
    medications: list[dict],
    pharmacy_name: str,
    pharmacy_address: str,
    tracking_code: str,
    tracking_link: str,
) -> tuple[str, str]:
    """Build email subject and HTML body for acute medication dispatch."""
    med_rows = ""
    for m in medications:
        med_rows += f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{m['name']}</td>"
        med_rows += f"<td style='padding:8px;border-bottom:1px solid #eee'>{m.get('strength','')}</td>"
        med_rows += f"<td style='padding:8px;border-bottom:1px solid #eee'>{m.get('dose','')}</td></tr>"

    subject = f"Your Medication Request {reference} - Leadway Health"

    body = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#fff;border:1px solid #eee;border-radius:8px;overflow:hidden">
        <div style="background:#C61531;padding:20px;text-align:center">
            <h1 style="color:#fff;margin:0;font-size:20px">LEADWAY Health</h1>
            <p style="color:#FFE0E0;margin:5px 0 0;font-size:13px">Medication Fulfilment Notification</p>
        </div>
        <div style="padding:25px">
            <p>Dear <strong>{member_name}</strong>,</p>
            <p>{facility_name} has submitted a medication request on your behalf through the Leadway Health portal.</p>

            <div style="background:#F8F9FA;border-radius:8px;padding:15px;margin:15px 0">
                <p style="margin:0 0 5px"><strong>Reference:</strong> {reference}</p>
                <p style="margin:0 0 5px"><strong>Diagnosis:</strong> {diagnosis}</p>
                <p style="margin:0"><strong>Type:</strong> Acute Medication</p>
            </div>

            <h3 style="color:#C61531;margin-top:20px">Medications Prescribed</h3>
            <table style="width:100%;border-collapse:collapse;font-size:14px">
                <tr style="background:#F4F5F7">
                    <th style="padding:8px;text-align:left">Medication</th>
                    <th style="padding:8px;text-align:left">Strength</th>
                    <th style="padding:8px;text-align:left">Dosage</th>
                </tr>
                {med_rows}
            </table>

            <h3 style="color:#C61531;margin-top:20px">Pharmacy Details</h3>
            <div style="background:#E8F8EE;border-radius:8px;padding:15px;border:1px solid #B5E8C9">
                <p style="margin:0 0 5px"><strong>Pharmacy:</strong> {pharmacy_name}</p>
                <p style="margin:0 0 5px"><strong>Address:</strong> {pharmacy_address}</p>
                <p style="margin:0"><strong>Tracking Code:</strong> <span style="font-size:18px;font-weight:bold;color:#0A7C3E">{tracking_code}</span></p>
            </div>

            <h3 style="color:#C61531;margin-top:20px">What Happens Next?</h3>
            <ol style="line-height:1.8;color:#555">
                <li>The pharmacy will confirm availability of your medications</li>
                <li>Once confirmed, you will receive a <strong>Pickup Code</strong></li>
                <li>Present the Pickup Code at the pharmacy to collect your medications</li>
            </ol>

            {"<p><a href='" + tracking_link + "' style='display:inline-block;background:#C61531;color:#fff;padding:10px 25px;border-radius:6px;text-decoration:none;font-weight:bold'>Track Your Order</a></p>" if tracking_link else ""}

            <p style="color:#999;font-size:12px;margin-top:25px">
                This is an automated notification from Leadway Health Services.<br>
                If you have questions, contact your healthcare provider or Leadway Health support.
            </p>
        </div>
        <div style="background:#F4F5F7;padding:15px;text-align:center;font-size:12px;color:#999">
            Leadway Health Services &mdash; For health, wealth &amp; more...
        </div>
    </div>
    """
    return subject, body


def send_member_notification(
    request_id: str,
    db: Session,
    pharmacy_name: str = "",
    pharmacy_address: str = "",
    tracking_code: str = "",
    tracking_link: str = "",
):
    """Send email notification to member after dispatch."""
    req = db.query(MedicationRequest).filter(MedicationRequest.request_id == request_id).first()
    if not req:
        return

    member_email = req.member_email
    if not member_email:
        logger.info("No email for member %s — skipping notification", req.enrollee_name)
        return

    items = db.query(MedicationRequestItem).filter(MedicationRequestItem.request_id == request_id).all()
    medications = [
        {"name": item.drug_name, "strength": item.strength or "", "dose": item.dosage_instruction or ""}
        for item in items
    ]

    subject, body = _build_acute_email(
        member_name=req.enrollee_name,
        member_email=member_email,
        facility_name=req.facility_name,
        reference=req.reference_number,
        diagnosis=req.diagnosis,
        medications=medications,
        pharmacy_name=pharmacy_name,
        pharmacy_address=pharmacy_address,
        tracking_code=tracking_code,
        tracking_link=tracking_link,
    )

    # For now, log the email. To send live, configure SMTP or use SendGrid/Mailgun
    # TODO: SMTP_INTEGRATION — connect to email service
    logger.info(
        "Member notification prepared: to=%s, ref=%s, tracking=%s",
        member_email, req.reference_number, tracking_code,
    )

    db.add(MedicationAuditLog(
        event_type="member_notified",
        request_id=request_id,
        detail=f"Email notification prepared for {member_email}. Tracking: {tracking_code}",
    ))
    db.flush()

    # TODO: Uncomment when SMTP is configured
    # try:
    #     msg = MIMEMultipart("alternative")
    #     msg["Subject"] = subject
    #     msg["From"] = "noreply@leadwayhealth.com"
    #     msg["To"] = member_email
    #     msg.attach(MIMEText(body, "html"))
    #     with smtplib.SMTP("smtp.gmail.com", 587) as server:
    #         server.starttls()
    #         server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    #         server.send_message(msg)
    #     logger.info("Email sent to %s", member_email)
    # except Exception as e:
    #     logger.error("Email send failed: %s", e)
