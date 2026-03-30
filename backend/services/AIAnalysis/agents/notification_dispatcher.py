import logging
import smtplib
import ssl
import asyncio
from email.message import EmailMessage
from typing import Dict, Optional
from services.AIAnalysis.shared.schemas import AnalysisResult
from services.AIAnalysis.utils.config import settings

logger = logging.getLogger(__name__)

class NotificationDispatcherAgent:
    def __init__(self):
        # external notification service removed; rely on SMTP only
        self.notification_service_url = None
        # SMTP config (expect these in settings)
        self.smtp_host = getattr(settings, "SMTP_HOST", None)
        self.smtp_port = getattr(settings, "SMTP_PORT", 587)
        self.smtp_user = getattr(settings, "SMTP_USER", None)
        self.smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        self.smtp_from = getattr(settings, "SMTP_FROM", "noreply@example.com")
        self.smtp_use_tls = getattr(settings, "SMTP_USE_TLS", True)
        self.smtp_enabled = bool(self.smtp_host and self.smtp_from)
    
    async def dispatch_notifications(self, analysis: AnalysisResult):
        """
        Send notifications to both citizen and assigned officer
        """
        # Always attempt to dispatch (SMTP is used for delivery)
        
        # Fetch citizen email using grievance_id -> grievance_forms -> user_id -> users
        citizen_email = await self._get_citizen_email(analysis.form_id)

        # Notification for citizen
        citizen_notification = self._create_citizen_notification(analysis, citizen_email)
        await self._send_notification(citizen_notification)
        
        # Notification for officer
        officer_notification = self._create_officer_notification(analysis)
        await self._send_notification(officer_notification)
    
    def _create_citizen_notification(self, analysis: AnalysisResult, email: Optional[str]) -> Dict:
        """Create notification payload for citizen"""
        if analysis.vector_check.is_duplicate:
            message = (
                f"Your grievance #{analysis.form_id} has been linked to an existing case "
                f"#{analysis.vector_check.parent_form_id}. You'll receive updates on the resolution."
            )
        else:
            message = (
                f"Your grievance #{analysis.form_id} has been assigned to "
                f"{analysis.routing.officer_name} ({analysis.routing.department}). "
                f"Expected response time: {analysis.routing.estimated_response_time}."
            )
        
        payload = {
            "recipient_type": "citizen",
            "recipient_id": analysis.form_id,  # retains grievance id mapping
            "notification_type": "grievance_update",
            "priority": analysis.priority_score.urgency_level,
            "title": "Grievance Status Update",
            "message": message,
            "metadata": {
                "form_id": analysis.form_id,
                "status": analysis.status,
            }
        }

        # Attach email if available so notification service can send email
        if email:
            payload["recipient_contact"] = {"email": email}
            payload["metadata"]["recipient_email"] = email
        else:
            logger.warning("Could not resolve citizen email for grievance %s", analysis.form_id)
        
        return payload
    
    def _create_officer_notification(self, analysis: AnalysisResult) -> Dict:
        """Create notification payload for officer"""
        # Don't notify officer if it's a duplicate
        if analysis.vector_check.is_duplicate:
            return None
        
        urgency_prefix = {
            "critical": "🚨 CRITICAL ALERT",
            "high": "⚠️ High Priority",
            "medium": "📋 New Assignment",
            "low": "📝 New Case"
        }.get(analysis.priority_score.urgency_level, "📋 New Assignment")
        
        message = (
            f"{urgency_prefix}: New grievance #{analysis.form_id} assigned to you. "
            f"Priority Score: {analysis.priority_score.score}/100. "
            f"Area: {analysis.vector_check.similarity_score or 'N/A'}. "
            f"Expected resolution: {analysis.routing.estimated_response_time}."
        )
        
        return {
            "recipient_type": "officer",
            "recipient_id": analysis.routing.officer_id,
            "notification_type": "new_assignment",
            "priority": analysis.priority_score.urgency_level,
            "title": f"New Grievance Assignment - {analysis.routing.department}",
            "message": message,
            "metadata": {
                "form_id": analysis.form_id,
                "priority_score": analysis.priority_score.score,
                "department": analysis.routing.department
            }
        }
    
    async def _get_citizen_email(self, grievance_id: str) -> Optional[str]:
        """
        Resolve citizen email by:
         1) Query grievance_forms collection for grievance_id -> get user_id
         2) Query users collection in user DB for user_id -> get email
        Returns email or None on failure.
        """
        try:
            # Attempt to import known DB getters; adapt to available project modules.
            try:
                from services.AIFormFilling.src.db.connection import get_database as get_grievance_db
            except Exception:
                logger.debug("grievance DB getter import failed, cannot fetch grievance_forms.")
                return None
            
            try:
                from services.user_service.src.db.connection import get_database as get_user_db
            except Exception:
                logger.debug("user DB getter import failed, cannot fetch users collection.")
                return None

            # Get grievance doc
            gdb = get_grievance_db()
            gcol = gdb.grievance_forms
            grievance_doc = await gcol.find_one({"_id": grievance_id}) or await gcol.find_one({"form_id": grievance_id})
            if not grievance_doc:
                logger.info("No grievance found for id %s", grievance_id)
                return None

            user_id = grievance_doc.get("user_id")
            if not user_id:
                logger.info("No user_id on grievance %s", grievance_id)
                return None

            # Get user email
            udb = get_user_db()
            ucol = udb.users
            user_doc = await ucol.find_one({"_id": user_id}) or await ucol.find_one({"user_id": user_id})
            if not user_doc:
                logger.info("No user found for user_id %s", user_id)
                return None

            email = user_doc.get("email")
            return email
        except Exception as e:
            logger.exception("Error resolving citizen email for grievance %s: %s", grievance_id, e)
            return None

    async def _send_notification(self, notification: Dict):
        """Send notification to notification service or via SMTP if configured"""
        if notification is None:
            return

        # Determine recipient email: prefer explicit contact, else try to resolve officer email
        recipient_contact = notification.get("recipient_contact", {})
        recipient_email = recipient_contact.get("email")
        subject = notification.get("title", "Notification")
        message_text = notification.get("message", "")

        if not recipient_email and notification.get("recipient_type") == "officer":
            # try to resolve officer email from superuser DB
            officer_id = notification.get("recipient_id")
            if officer_id:
                try:
                    recipient_email = await self._get_officer_email(officer_id)
                except Exception:
                    logger.exception("Error resolving officer email for %s", officer_id)

        if not recipient_email:
            logger.warning("No recipient email found; skipping notification (metadata form_id=%s).", notification.get("metadata", {}).get("form_id"))
            return

        if not self.smtp_enabled:
            logger.error("SMTP not configured; cannot send email to %s", recipient_email)
            return

        try:
            await self._send_email_via_smtp(recipient_email, subject, message_text, notification.get("metadata", {}))
            logger.info("Sent SMTP notification to %s", recipient_email)
        except Exception:
            logger.exception("Error sending SMTP notification to %s", recipient_email)

    async def _send_email_via_smtp(self, to_email: str, subject: str, body: str, metadata: Dict):
        """Async wrapper that runs the blocking SMTP send in a thread."""
        await asyncio.to_thread(self._smtp_send, to_email, subject, body, metadata)
    
    def _smtp_send(self, to_email: str, subject: str, body: str, metadata: Dict):
        """Blocking SMTP send using smtplib and email.message.EmailMessage."""
        if not self.smtp_enabled:
            raise RuntimeError("SMTP is not configured.")

        msg = EmailMessage()
        msg["From"] = self.smtp_from
        msg["To"] = to_email
        msg["Subject"] = subject
        # Include metadata in body footer if present
        footer = ""
        if metadata:
            footer = "\n\n---\nMetadata:\n" + "\n".join(f"{k}: {v}" for k, v in metadata.items())
        msg.set_content(f"{body}{footer}")

        context = ssl.create_default_context()
        # Use SMTP_SSL if common port 465 is used, otherwise use SMTP + STARTTLS when enabled.
        if self.smtp_use_tls and int(self.smtp_port) == 465:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                if self.smtp_use_tls:
                    server.starttls(context=context)
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

    async def _get_officer_email(self, officer_id: str) -> Optional[str]:
        """Lookup officer email in superuser staff_users collection by id."""
        try:
            try:
                from services.superuser_services.db.connection import get_database as get_superuser_db
            except Exception:
                logger.debug("superuser DB getter import failed; cannot fetch officer email.")
                return None

            db = get_superuser_db()
            col = db.staff_users
            doc = await col.find_one({"_id": officer_id}) or await col.find_one({"officer_id": officer_id})
            if not doc:
                return None
            # Try common fields for email
            return doc.get("email") or doc.get("contact", {}).get("email")
        except Exception:
            logger.exception("Error fetching officer email for %s", officer_id)
            return None
