import os
import smtplib
import ssl
import logging
import asyncio
from email.message import EmailMessage
from typing import Optional

logger = logging.getLogger(__name__)

class OfficerNotificationService:
    """Notify citizens when officers request clarifications or resolve tickets."""
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
        self.smtp_user = os.getenv("SMTP_USERNAME")
        self.smtp_pass = os.getenv("SMTP_PASSWORD")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)
        self.smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")
        self.smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() in ("1", "true", "yes")

    async def _send_message(self, to_email: str, subject: str, body: str) -> bool:
        if not self.smtp_host or not self.smtp_port:
            logger.warning("SMTP not configured for OfficerResolutionService; simulated send")
            logger.info(f"Simulated email to {to_email}: {subject}")
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
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_clarification_email(
        self,
        to_email: str,
        grievance_id: str,
        officer_id: str,
        message: str,
    ) -> bool:
        subject = f"Clarification requested for grievance {grievance_id}"
        body = f"""Dear Citizen,

An officer ({officer_id}) has requested a clarification for your grievance (ID: {grievance_id}).

Message from officer:
{message}

Please log in to the portal and respond to the clarification.

Best regards,
Government Portal Team
"""
        return await self._send_message(to_email, subject, body)

    async def send_resolution_email(
        self,
        to_email: str,
        grievance_id: str,
        officer_id: str,
        action_taken: str,
        closing_remark: Optional[str] = None
    ) -> bool:
        subject = f"Your grievance {grievance_id} has been resolved"
        closing_line = f"Closing remark: {closing_remark}\n" if closing_remark else ""
        body = f"""Dear Citizen,

Your grievance (ID: {grievance_id}) has been marked resolved by officer {officer_id}.

Action taken:
{action_taken}

{closing_line}You can log in to the portal to view resolution details and provide feedback.

Best regards,
Government Portal Team
"""
        return await self._send_message(to_email, subject, body)

officer_notification_service = OfficerNotificationService()
