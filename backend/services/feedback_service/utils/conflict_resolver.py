from typing import Dict, Optional
from ..db.feedback_db import feedback_db
import logging

logger = logging.getLogger(__name__)

class ConflictResolver:
    
    async def process_feedback(self, feedback_data: dict, evidence_path: Optional[str] = None, sentiment: Optional[dict] = None) -> Dict[str, any]:
        """
        Main conflict resolution logic (simplified without AI)
        sentiment: dict like {"label":"negative","score":0.8,"explanation":"..."} (score: higher = more negative)
        Negative sentiment now forces a conflict_detected = True.
        """
        conflict_detected = False
        escalated = False
        message = None
        
        # Get grievance details
        grievance = await feedback_db.get_grievance_details(feedback_data["form_id"])
        if not grievance:
            return {"error": "Grievance not found"}
        
        # Check for positive feedback (happy path)
        if (feedback_data["is_resolved_by_user"] and 
            feedback_data["ratings"]["overall"] > 3):
            # Final close - citizen is satisfied
            await feedback_db.update_grievance_status(
                feedback_data["form_id"], 
                "closed"
            )
            return {
                "conflict_detected": False,
                "escalated": False,
                "action": "closed",
                "message": "Ticket closed - citizen satisfied",
                "sentiment": sentiment
            }
        
        # Determine whether sentiment is negative (strong negative label or high negative score)
        negative_sentiment = False
        try:
            if sentiment:
                negative_sentiment = (
                    (isinstance(sentiment.get("label"), str) and sentiment.get("label").lower() == "negative")
                    or (isinstance(sentiment.get("score"), (int, float)) and sentiment.get("score", 0) > 0.6)
                )
        except Exception:
            negative_sentiment = False

        # If the user reports not resolved OR sentiment is negative, treat as a conflict
        if (not feedback_data["is_resolved_by_user"]) or negative_sentiment:
            conflict_detected = True
            if negative_sentiment and feedback_data["is_resolved_by_user"]:
                # user marked resolved but sentiment negative -> keep as conflict and log
                logger.info("Feedback %s marked as conflict due to negative sentiment", feedback_data.get("form_id"))
                message = "Conflict detected due to negative sentiment"
            
            # escalate on low rating OR strong negative sentiment
            low_rating = feedback_data["ratings"]["overall"] <= 2
            if low_rating or negative_sentiment:
                escalated = True
                await self._escalate_ticket(feedback_data["form_id"], grievance.get("officer_id"))
                if not message:
                    message = "Escalated due to low rating or negative sentiment"
        
        # Update feedback data with conflict resolution results (persisted later)
        feedback_data.update({
            "conflict_detected": conflict_detected,
            "escalated": escalated
        })
        
        return {
            "conflict_detected": conflict_detected,
            "escalated": escalated,
            "action": "escalated" if escalated else "reopened",
            "sentiment": sentiment,
            "message": message
        }
    
    async def _escalate_ticket(self, form_id: str, officer_id: str):
        """Escalate ticket to department admin"""
        try:
            await feedback_db.update_grievance_status(
                form_id, 
                "escalated", 
                escalated=True
            )
            
            # TODO: Send notification to department admin
            # await notification_service.notify_admin(officer_id, form_id)
            
            logger.info(f"Escalated ticket {form_id} for officer {officer_id}")
            
        except Exception as e:
            logger.error(f"Failed to escalate ticket {form_id}: {str(e)}")

conflict_resolver = ConflictResolver()
