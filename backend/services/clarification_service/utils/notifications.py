import os
import smtplib
import ssl
import logging
import asyncio
from email.message import EmailMessage
from typing import Optional
from shared.firebase_client import get_firestore_client

logger = logging.getLogger(__name__)

class ClarificationNotificationService:
    """Service to notify citizens when an officer files a clarification via email."""
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587")) if os.getenv("SMTP_PORT") else None
        self.smtp_user = os.getenv("SMTP_USERNAME")
        self.smtp_pass = os.getenv("SMTP_PASSWORD")
        self.smtp_from = os.getenv("SMTP_FROM", self.smtp_user)
        self.smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes")
        self.smtp_starttls = os.getenv("SMTP_STARTTLS", "true").lower() in ("1", "true", "yes")
        self.db = get_firestore_client()

    async def get_citizen_email(self, grievance_id: str) -> Optional[str]:
        """Fetch citizen email by querying grievance_forms for user_id, then users for email."""
        try:
            # Try by document ID first
            doc_ref = self.db.collection("grievance_forms").document(grievance_id)
            doc = await doc_ref.get()
            grievance = doc.to_dict() if doc.exists else None
            
            # Fallback to field query
            if not grievance:
                docs = self.db.collection("grievance_forms").where("form_id", "==", grievance_id).limit(1).stream()
                async for d in docs:
                    grievance = d.to_dict()
                    break
                    
            if not grievance:
                logger.warning(f"Grievance {grievance_id} not found")
                return None
                
            user_id = grievance.get("user_id")
            if not user_id:
                logger.warning(f"No user_id found for grievance {grievance_id}")
                return None
                
            # Try fetching user by user_id
            user_doc = await self.db.collection("users").document(user_id).get()
            if user_doc.exists:
                return user_doc.to_dict().get("email")
                
            # Fallback to field query for user
            user_docs = self.db.collection("users").where("user_id", "==", user_id).limit(1).stream()
            async for ud in user_docs:
                return ud.to_dict().get("email")
                
            logger.warning(f"User {user_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error fetching citizen email: {e}")
            return None

    async def send_clarification_email(
        self,
        grievance_id: str,
        officer_id: str,
        message: str,
        resolution_id: Optional[str] = None,
        to_email: Optional[str] = None
    ) -> bool:
        """Send clarification email to citizen. Returns True on success, False on failure."""
        # Use provided email or fetch from DB
        recipient = to_email or await self.get_citizen_email(grievance_id)
        if not recipient:
            logger.error(f"Could not fetch email for grievance {grievance_id}")
            return False
            
        subject = f"Clarification requested for grievance {grievance_id}"
        resolution_line = f"Resolution ID: {resolution_id}\n" if resolution_id else ""
        body = f"""Dear Citizen,

An officer ({officer_id}) has requested a clarification for your grievance (ID: {grievance_id}).
{resolution_line}Message from officer:
{message}

Please log in to the portal to respond.

Best regards,
Government Portal Team
"""

        if not self.smtp_host or not self.smtp_port:
            logger.info(f"Simulated clarification email to {recipient}: {subject}")
            await asyncio.sleep(0.1)
            return True

        msg = EmailMessage()
        msg["From"] = self.smtp_from or self.smtp_user or "no-reply@example.com"
        msg["To"] = recipient
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
            logger.info(f"Clarification email sent to {recipient} for grievance {grievance_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send clarification email to {recipient}: {e}")
            return False

clarification_notification_service = ClarificationNotificationService()

