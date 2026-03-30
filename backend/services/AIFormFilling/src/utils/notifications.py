import os
import smtplib
import ssl
import logging
import asyncio
from email.message import EmailMessage
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AIFormNotificationService:
    """Service to notify citizens when their grievance is submitted."""
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
        self.smtp_user = os.getenv("SMTP_USERNAME")
        self.smtp_pass = os.getenv("SMTP_PASSWORD")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)
        self.smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")
        self.smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() in ("1", "true", "yes")

    async def send_ticket_email(self, to_email: str, form_id: str, form_data: Dict[str, Any]) -> bool:
        """Send a submission confirmation email with ticket id and short summary."""
        subject = f"Your grievance has been submitted — Reference ID: {form_id}"
        # Build a short summary: pick a few meaningful keys if present
        summary_keys = ["title", "category", "description", "address", "status"]
        summary_lines = []
        for k in summary_keys:
            if k in form_data and form_data[k]:
                summary_lines.append(f"{k.capitalize()}: {form_data[k]}")
        # Fallback to a compact JSON snippet if nothing obvious found
        if not summary_lines:
            try:
                import json
                compact = json.dumps({k: form_data.get(k) for k in list(form_data)[:5]}, ensure_ascii=False)
            except Exception:
                compact = "<summary unavailable>"
            summary_lines = [compact]

        body = f"""Dear Citizen,

Your grievance has been submitted successfully.

Reference ID: {form_id}

Summary:
{chr(10).join(summary_lines)}

You can use the Reference ID to track the status of your grievance.

Best regards,
Government Portal Team
"""

        if not self.smtp_host or not self.smtp_port:
            logger.warning("SMTP config missing for AIFormFilling service; using simulated send")
            logger.info(f"Simulated ticket email to {to_email}: {subject}")
            await asyncio.sleep(0.1)
            return True

        msg = EmailMessage()
        msg["From"] = self.smtp_from or self.smtp_user or "no-reply@example.com"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        def _send():
            if self.smtp_use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as s:
                    if self.smtp_user and self.smtp_pass:
                        s.login(self.smtp_user, self.smtp_pass)
                    s.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as s:
                    s.ehlo()
                    if self.smtp_starttls:
                        context = ssl.create_default_context()
                        s.starttls(context=context)
                        s.ehlo()
                    if self.smtp_user and self.smtp_pass:
                        s.login(self.smtp_user, self.smtp_pass)
                    s.send_message(msg)
            return True

        try:
            await asyncio.to_thread(_send)
            logger.info(f"Ticket email sent to {to_email} for form {form_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send ticket email to {to_email} for form {form_id}: {e}")
            return False

ai_notification_service = AIFormNotificationService()
