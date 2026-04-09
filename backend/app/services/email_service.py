"""
Email service for sending claim confirmation emails via SMTP.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

log = logging.getLogger(__name__)


def _send_email(to_emails: list[str], subject: str, html_body: str) -> bool:
    """Send an HTML email via SMTP. Returns True on success."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        log.warning("SMTP not configured — skipping email")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
        msg["To"] = ", ".join(to_emails)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], to_emails, msg.as_string())

        log.info("Email sent to %s: %s", to_emails, subject)
        return True
    except Exception as e:
        log.error("Failed to send email: %s", e)
        return False


def send_claim_confirmation(
    member_email: str,
    enrollee_name: str,
    enrollee_id: str,
    pa_code: str,
    visit_type: str,
    provider_name: str,
    visit_date: str,
    claim_amount: float,
    approved_amount: float,
    bank_name: str,
    account_number: str,
    account_name: str,
    reason_for_visit: str,
    remarks: str,
    reimbursement_reason: str,
    batch_number: str | None = None,
    prognosis_status: str | None = None,
):
    """
    Send confirmation email to member (and CC claims team) after
    a reimbursement claim is submitted to Prognosis.
    """
    masked_acct = f"****{account_number[-4:]}" if len(account_number) >= 4 else account_number

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 650px; margin: 0 auto; color: #333;">
      <div style="background: linear-gradient(135deg, #C61531 0%, #8B0E22 100%); padding: 24px 32px; border-radius: 12px 12px 0 0;">
        <h1 style="color: #fff; margin: 0; font-size: 20px;">LEADWAY <span style="color: #FFCE07;">Health</span></h1>
        <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px;">Reimbursement Claim Confirmation</p>
      </div>

      <div style="background: #fff; padding: 28px 32px; border: 1px solid #eee; border-top: none;">
        <p style="font-size: 15px;">Dear <strong>{enrollee_name}</strong>,</p>
        <p style="font-size: 14px; color: #555; line-height: 1.6;">
          Your reimbursement claim has been submitted successfully. Below are the details of your submission.
        </p>

        {f'''<div style="background: #E8F8EE; border: 1px solid #B5E8C9; border-radius: 8px; padding: 14px 18px; margin: 16px 0;">
          <span style="color: #0A7C3E; font-weight: 700; font-size: 13px;">PROGNOSIS BATCH NUMBER</span>
          <div style="font-size: 22px; font-weight: 800; color: #0A7C3E; letter-spacing: 0.04em;">{batch_number}</div>
        </div>''' if batch_number else ''}

        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
          <tr style="border-bottom: 1px solid #f0f0f0;">
            <td style="padding: 10px 0; color: #888; width: 40%;">PA Code</td>
            <td style="padding: 10px 0; font-weight: 700; color: #C61531;">{pa_code}</td>
          </tr>
          <tr style="border-bottom: 1px solid #f0f0f0;">
            <td style="padding: 10px 0; color: #888;">Enrollee ID</td>
            <td style="padding: 10px 0; font-weight: 600;">{enrollee_id}</td>
          </tr>
          <tr style="border-bottom: 1px solid #f0f0f0;">
            <td style="padding: 10px 0; color: #888;">Visit Type</td>
            <td style="padding: 10px 0; font-weight: 600;">{visit_type}</td>
          </tr>
          <tr style="border-bottom: 1px solid #f0f0f0;">
            <td style="padding: 10px 0; color: #888;">Healthcare Provider</td>
            <td style="padding: 10px 0; font-weight: 600;">{provider_name}</td>
          </tr>
          <tr style="border-bottom: 1px solid #f0f0f0;">
            <td style="padding: 10px 0; color: #888;">Visit Date</td>
            <td style="padding: 10px 0; font-weight: 600;">{visit_date}</td>
          </tr>
          <tr style="border-bottom: 1px solid #f0f0f0;">
            <td style="padding: 10px 0; color: #888;">Approved Amount</td>
            <td style="padding: 10px 0; font-weight: 600;">NGN {approved_amount:,.2f}</td>
          </tr>
          <tr style="border-bottom: 1px solid #f0f0f0;">
            <td style="padding: 10px 0; color: #888;">Claim Amount</td>
            <td style="padding: 10px 0; font-weight: 800; font-size: 16px; color: #0A7C3E;">NGN {claim_amount:,.2f}</td>
          </tr>
          {f'<tr style="border-bottom: 1px solid #f0f0f0;"><td style="padding: 10px 0; color: #888;">Reimbursement Reason</td><td style="padding: 10px 0;">{reimbursement_reason}</td></tr>' if reimbursement_reason else ''}
          <tr style="border-bottom: 1px solid #f0f0f0;">
            <td style="padding: 10px 0; color: #888;">Reason for Visit</td>
            <td style="padding: 10px 0;">{reason_for_visit}</td>
          </tr>
          {f'<tr style="border-bottom: 1px solid #f0f0f0;"><td style="padding: 10px 0; color: #888;">Remarks</td><td style="padding: 10px 0;">{remarks}</td></tr>' if remarks else ''}
        </table>

        <div style="background: #F8F9FA; border-radius: 8px; padding: 14px 18px; margin: 16px 0;">
          <span style="font-size: 12px; color: #888; text-transform: uppercase; font-weight: 600;">Payment Details</span>
          <div style="margin-top: 6px; font-size: 14px;">
            <strong>{bank_name}</strong><br/>
            Account: {masked_acct}<br/>
            Name: {account_name}
          </div>
        </div>

        {f'<p style="font-size: 13px; color: #888;">Prognosis Status: {prognosis_status}</p>' if prognosis_status else ''}

        <p style="font-size: 14px; color: #555; line-height: 1.6; margin-top: 20px;">
          Your claim is now under review. You will be notified once it has been processed.
          If you have questions, please contact the Leadway Health call center.
        </p>
      </div>

      <div style="background: #F4F5F7; padding: 16px 32px; border-radius: 0 0 12px 12px; text-align: center; border: 1px solid #eee; border-top: none;">
        <p style="color: #999; font-size: 12px; margin: 0;">Leadway Health Services &mdash; For health, wealth &amp; more...</p>
      </div>
    </div>
    """

    subject = f"Reimbursement Claim Confirmation — {pa_code}"
    if batch_number:
        subject = f"Reimbursement Claim {batch_number} — {pa_code}"

    # Collect recipients: member + claims team
    recipients = []
    if member_email:
        recipients.append(member_email)
    if settings.CLAIMS_TEAM_EMAIL:
        recipients.append(settings.CLAIMS_TEAM_EMAIL)

    if not recipients:
        log.warning("No email recipients — skipping claim confirmation email")
        return False

    return _send_email(recipients, subject, html)
