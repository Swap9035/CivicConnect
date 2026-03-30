import logging
from typing import Dict, Any
import asyncio
import os
import smtplib
import ssl
from email.message import EmailMessage

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications (Email/SMS)"""
    
    def __init__(self):
        # Read SMTP config from env; leave unset to use simulated send (good for local/dev)
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
        self.smtp_user = os.getenv("SMTP_USERNAME")
        self.smtp_pass = os.getenv("SMTP_PASSWORD")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)
        self.smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")
        self.smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() in ("1", "true", "yes")
    
    async def send_credentials_email(self, email: str, temp_password: str, full_name: str) -> bool:
        """Send temporary password via email using SMTP (falls back to simulated send if not configured)"""
        subject = "Your government portal account has been created"
        body = f"""Dear {full_name},

Your government portal account has been created successfully.

Login Details:
Email: {email}
Temporary Password: {temp_password}

Please log in and change your password immediately for security.

Best regards,
Government Portal Team
"""
        # If SMTP not configured, keep previous simulated behavior for local/dev
        if not self.smtp_host or not self.smtp_port:
            logger.warning("SMTP config missing, using simulated email send")
            logger.info(f"Simulated email to {email} with temporary password")
            await asyncio.sleep(0.1)
            return True

        msg = EmailMessage()
        msg["From"] = self.smtp_from or self.smtp_user or "no-reply@example.com"
        msg["To"] = email
        msg["Subject"] = subject
        msg.set_content(body)

        def _send_via_smtp():
            try:
                if self.smtp_use_ssl:
                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                        if self.smtp_user and self.smtp_pass:
                            server.login(self.smtp_user, self.smtp_pass)
                        server.send_message(msg)
                else:
                    with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                        server.ehlo()
                        if self.smtp_starttls:
                            context = ssl.create_default_context()
                            server.starttls(context=context)
                            server.ehlo()
                        if self.smtp_user and self.smtp_pass:
                            server.login(self.smtp_user, self.smtp_pass)
                        server.send_message(msg)
                return True
            except Exception as e:
                # Re-raise to be caught by outer async wrapper
                raise

        try:
            await asyncio.to_thread(_send_via_smtp)
            logger.info(f"Email sent to {email} with temporary password via SMTP")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {email} via SMTP: {e}")
            return False
    
    async def send_credentials_sms(self, phone_number: str, temp_password: str) -> bool:
        """Send temporary password via SMS"""
        try:
            # In a real implementation, integrate with SMS service (Twilio, AWS SNS, etc.)
            message = f"Your govt portal password: {temp_password}. Login & change it immediately."
            
            # Simulate SMS sending
            logger.info(f"SMS sent to {phone_number} with temporary password")
            await asyncio.sleep(0.1)  # Simulate network delay
            
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return False
    
    async def send_credentials(self, user_data: Dict[str, Any], temp_password: str) -> Dict[str, bool]:
        """Send credentials via both email and SMS"""
        results = {
            "email_sent": False,
            "sms_sent": False
        }
        
        # Send email
        email_task = self.send_credentials_email(
            user_data["email"], 
            temp_password, 
            user_data["full_name"]
        )
        
        # Send SMS
        sms_task = self.send_credentials_sms(
            user_data["phone_number"], 
            temp_password
        )
        
        print("Password", temp_password)
        # Execute both tasks concurrently
        email_result, sms_result = await asyncio.gather(
            email_task, sms_task, return_exceptions=True
        )
        
        results["email_sent"] = email_result if isinstance(email_result, bool) else False
        results["sms_sent"] = sms_result if isinstance(sms_result, bool) else False
        
        return results

notification_service = NotificationService()
