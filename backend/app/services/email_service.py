"""
Email Service — sends reimbursement claim data to the claims team
via the Prognosis SendEmailAlert API.

POST /api/EnrolleeProfile/SendEmailAlert
Uses the same Prognosis auth token. Files are base64-encoded in Attachments.
"""

import base64
import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0)


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


async def _get_prognosis_token() -> str | None:
    """Get Prognosis auth token (reuses prognosis_client cached token)."""
    from app.services.prognosis_client import _get_prognosis_token
    return await _get_prognosis_token()


def send_claim_email(
    claim_data: dict,
    attachments: list[tuple[str, bytes, str]] | None = None,
) -> bool:
    """
    Send a reimbursement claim email via Prognosis SendEmailAlert API.

    POST /api/EnrolleeProfile/SendEmailAlert

    Args:
        claim_data: Dict with all claim fields
        attachments: List of (filename, file_bytes, content_type) tuples.
                     Files are base64-encoded for the API, then discarded.

    Returns True if sent successfully, False otherwise.
    """
    import asyncio

    attachments = attachments or []
    claim_data["attachment_count"] = len(attachments)

    if not settings.CLAIMS_EMAIL:
        log.warning(
            "CLAIMS_EMAIL not configured — claim email for %s logged only.",
            claim_data.get("claim_ref"),
        )
        _log_plain_text(claim_data, attachments)
        return True  # Treat as success in dev mode

    # Build email payload
    html_body = _build_claim_html(claim_data)

    # Base64-encode attachments for the API
    api_attachments = None
    if attachments:
        api_attachments = [
            {
                "FileName": fname,
                "ContentType": ctype,
                "Base64Content": base64.b64encode(fbytes).decode("utf-8"),
            }
            for fname, fbytes, ctype in attachments
        ]

    payload = {
        "EmailAddress": settings.CLAIMS_EMAIL,
        "CC": "",
        "BCC": "",
        "Subject": (
            f"REIMBURSEMENT CLAIM: {claim_data.get('claim_ref', '')} "
            f"- {claim_data.get('member_name', 'Unknown')} "
            f"({claim_data.get('enrollee_id', '')})"
        ),
        "MessageBody": html_body,
        "Attachments": api_attachments,
        "Category": "Reimbursement",
        "UserId": 0,
        "ProviderId": 0,
        "ServiceId": 0,
        "Reference": claim_data.get("claim_ref", ""),
        "TransactionType": "ReimbursementClaim",
    }

    # Send via Prognosis API
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_send_email_api(payload))
        loop.close()
        return result
    except Exception as e:
        log.error("Email send failed for %s: %s", claim_data.get("claim_ref"), e)
        return False


async def _send_email_api(payload: dict) -> bool:
    """Call the Prognosis SendEmailAlert endpoint."""
    if not settings.PROGNOSIS_BASE_URL:
        log.warning("PROGNOSIS_BASE_URL not configured — cannot send email")
        return False

    token = await _get_prognosis_token()
    if not token:
        log.error("Cannot send email — Prognosis auth failed")
        return False

    url = f"{settings.PROGNOSIS_BASE_URL}/api/EnrolleeProfile/SendEmailAlert"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code == 200:
            log.info(
                "Claim email sent via Prognosis API: ref=%s to=%s",
                payload.get("Reference"),
                payload.get("EmailAddress"),
            )
            return True
        else:
            log.error(
                "Prognosis SendEmailAlert failed: status=%d body=%s",
                resp.status_code,
                resp.text[:300],
            )
            return False
    except httpx.RequestError as e:
        log.error("Prognosis SendEmailAlert request failed: %s", e)
        return False


def _log_plain_text(claim_data: dict, attachments: list) -> None:
    """Dev-mode fallback: log claim details to console."""
    log.info(
        "CLAIM EMAIL (dev mode): ref=%s member=%s (%s) amount=NGN %s attachments=%d",
        claim_data.get("claim_ref"),
        claim_data.get("member_name"),
        claim_data.get("enrollee_id"),
        f"{claim_data.get('claim_amount', 0):,.2f}",
        len(attachments),
    )
    for fname, fbytes, ctype in attachments:
        log.info("  ATTACHMENT: %s (%d bytes, %s)", fname, len(fbytes), ctype)
