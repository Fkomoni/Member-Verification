"""
Email Service — sends reimbursement claim data + document attachments
to the claims team email. Files are attached and then discarded (never stored).

Uses SMTP when configured, falls back to logging in dev mode.
"""

import logging
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

log = logging.getLogger(__name__)


def _build_claim_html(claim_data: dict) -> str:
    """Build a formatted HTML email body from claim data."""
    svc_rows = ""
    for line in claim_data.get("service_lines", []):
        svc_rows += (
            f"<tr>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee'>{line['service_name']}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;text-align:center'>{line['quantity']}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;text-align:right'>&#8358;{line['unit_price']:,.2f}</td>"
            f"<td style='padding:6px 10px;border-bottom:1px solid #eee;text-align:right'>&#8358;{line['quantity'] * line['unit_price']:,.2f}</td>"
            f"</tr>"
        )

    svc_table = ""
    if svc_rows:
        svc_table = f"""
        <h3 style="color:#C61531;margin:20px 0 8px">Services Rendered</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px">
            <thead>
                <tr style="background:#F4F5F7">
                    <th style="padding:8px 10px;text-align:left">Service</th>
                    <th style="padding:8px 10px;text-align:center">Qty</th>
                    <th style="padding:8px 10px;text-align:right">Unit Price</th>
                    <th style="padding:8px 10px;text-align:right">Total</th>
                </tr>
            </thead>
            <tbody>{svc_rows}</tbody>
        </table>
        """

    amount_flag = ""
    if claim_data.get("amount_flag"):
        amount_flag = f"""
        <div style="background:#FFF8E6;border:1px solid #F5DFA0;border-radius:6px;padding:10px 14px;margin:12px 0;color:#8B6914;font-size:13px">
            <strong>AMOUNT FLAG:</strong> {claim_data['amount_flag']}
        </div>
        """

    return f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:680px;margin:0 auto">
        <div style="background:linear-gradient(135deg,#C61531,#8B0E22);padding:24px 28px;border-radius:10px 10px 0 0">
            <h1 style="color:#fff;margin:0;font-size:20px">Reimbursement Claim Submitted</h1>
            <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:14px">Claim Ref: {claim_data.get('claim_ref', 'N/A')}</p>
        </div>

        <div style="background:#fff;padding:24px 28px;border:1px solid #eee;border-top:none;border-radius:0 0 10px 10px">
            {amount_flag}

            <h3 style="color:#C61531;margin:0 0 8px">Member Details</h3>
            <table style="font-size:13px;margin-bottom:16px">
                <tr><td style="padding:3px 16px 3px 0;color:#888">Name:</td><td><strong>{claim_data.get('member_name', 'N/A')}</strong></td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Enrollee ID:</td><td>{claim_data.get('enrollee_id', 'N/A')}</td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Phone:</td><td>{claim_data.get('member_phone', 'N/A')}</td></tr>
            </table>

            <h3 style="color:#C61531;margin:16px 0 8px">Authorization</h3>
            <table style="font-size:13px;margin-bottom:16px">
                <tr><td style="padding:3px 16px 3px 0;color:#888">Code:</td><td><strong style="font-family:monospace;font-size:14px">{claim_data.get('authorization_code', 'N/A')}</strong></td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Approved Amount:</td><td><strong>&#8358;{claim_data.get('approved_amount', 0):,.2f}</strong></td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Agent:</td><td>{claim_data.get('agent_name', 'N/A')}</td></tr>
            </table>

            <h3 style="color:#C61531;margin:16px 0 8px">Claim Details</h3>
            <table style="font-size:13px;margin-bottom:16px">
                <tr><td style="padding:3px 16px 3px 0;color:#888">Reimbursement Reason:</td><td>{claim_data.get('reimbursement_reason', 'N/A')}</td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Hospital:</td><td><strong>{claim_data.get('hospital_name', 'N/A')}</strong></td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Visit Date:</td><td>{claim_data.get('visit_date', 'N/A')}</td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Reason for Visit:</td><td>{claim_data.get('reason_for_visit', 'N/A')}</td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Claim Amount:</td><td><strong style="font-size:15px">&#8358;{claim_data.get('claim_amount', 0):,.2f}</strong></td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Medications:</td><td>{claim_data.get('medications') or '—'}</td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Lab Investigations:</td><td>{claim_data.get('lab_investigations') or '—'}</td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Comments:</td><td>{claim_data.get('comments') or '—'}</td></tr>
            </table>

            {svc_table}

            <h3 style="color:#C61531;margin:20px 0 8px">Bank Details</h3>
            <table style="font-size:13px;margin-bottom:16px">
                <tr><td style="padding:3px 16px 3px 0;color:#888">Bank:</td><td>{claim_data.get('bank_name', 'N/A')}</td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Account No:</td><td>{claim_data.get('account_number', 'N/A')}</td></tr>
                <tr><td style="padding:3px 16px 3px 0;color:#888">Account Name:</td><td><strong>{claim_data.get('account_name', 'N/A')}</strong></td></tr>
            </table>

            <div style="margin-top:20px;padding-top:16px;border-top:1px solid #eee;font-size:12px;color:#aaa">
                <p>Attached documents: {claim_data.get('attachment_count', 0)} file(s)</p>
                <p>Submitted via Leadway Health Reimbursement Portal</p>
            </div>
        </div>
    </div>
    """


def send_claim_email(
    claim_data: dict,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> bool:
    """
    Send a reimbursement claim email to the claims team.

    Args:
        claim_data: Dict with all claim fields (claim_ref, member_name, etc.)
        attachments: List of (filename, file_bytes, content_type) tuples.
                     Files are read into memory, attached, and never persisted.

    Returns True if sent successfully, False otherwise.
    """
    attachments = attachments or []
    claim_data["attachment_count"] = len(attachments)

    # If SMTP is not configured, log and return
    if not settings.SMTP_HOST or not settings.CLAIMS_EMAIL:
        log.warning(
            "SMTP not configured — claim email for %s logged instead of sent. "
            "Set SMTP_HOST and CLAIMS_EMAIL to enable.",
            claim_data.get("claim_ref"),
        )
        log.info("CLAIM EMAIL BODY (dev mode):\n%s", _format_plain_text(claim_data))
        for fname, fbytes, ctype in attachments:
            log.info("  ATTACHMENT: %s (%d bytes, %s)", fname, len(fbytes), ctype)
        return True  # Treat as success in dev mode

    # Build email
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = settings.CLAIMS_EMAIL
    msg["Subject"] = (
        f"Reimbursement Claim {claim_data.get('claim_ref', '')} "
        f"— {claim_data.get('member_name', 'Unknown')} "
        f"({claim_data.get('enrollee_id', '')})"
    )

    # HTML body
    html_body = _build_claim_html(claim_data)
    msg.attach(MIMEText(html_body, "html"))

    # Attach files
    for filename, file_bytes, content_type in attachments:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(file_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    # Send via SMTP
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.ehlo()
            if settings.SMTP_PORT == 587:
                server.starttls()
                server.ehlo()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.SMTP_FROM_EMAIL,
                [settings.CLAIMS_EMAIL],
                msg.as_string(),
            )
        log.info(
            "Claim email sent: ref=%s to=%s attachments=%d",
            claim_data.get("claim_ref"),
            settings.CLAIMS_EMAIL,
            len(attachments),
        )
        return True
    except Exception as e:
        log.error("Failed to send claim email for %s: %s", claim_data.get("claim_ref"), e)
        return False


def _format_plain_text(claim_data: dict) -> str:
    """Plain-text fallback for dev logging."""
    lines = [
        f"=== REIMBURSEMENT CLAIM: {claim_data.get('claim_ref', 'N/A')} ===",
        f"Member: {claim_data.get('member_name')} ({claim_data.get('enrollee_id')})",
        f"Phone: {claim_data.get('member_phone')}",
        f"Auth Code: {claim_data.get('authorization_code')}",
        f"Approved Amount: NGN {claim_data.get('approved_amount', 0):,.2f}",
        f"Claim Amount: NGN {claim_data.get('claim_amount', 0):,.2f}",
        f"Hospital: {claim_data.get('hospital_name')}",
        f"Visit Date: {claim_data.get('visit_date')}",
        f"Reason: {claim_data.get('reason_for_visit')}",
        f"Reimbursement Reason: {claim_data.get('reimbursement_reason')}",
        f"Medications: {claim_data.get('medications') or '—'}",
        f"Lab: {claim_data.get('lab_investigations') or '—'}",
        f"Bank: {claim_data.get('bank_name')} / {claim_data.get('account_number')} / {claim_data.get('account_name')}",
        f"Attachments: {claim_data.get('attachment_count', 0)}",
    ]
    if claim_data.get("amount_flag"):
        lines.insert(2, f"*** AMOUNT FLAG: {claim_data['amount_flag']} ***")
    return "\n".join(lines)
