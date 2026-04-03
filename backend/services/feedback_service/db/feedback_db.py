from typing import List, Optional
import os
from shared.firebase_client import get_firestore_client
import uuid
from datetime import datetime, timezone
import logging
from google.cloud import firestore

logger = logging.getLogger(__name__)

class FeedbackDatabase:
    def __init__(self):
        self.db = get_firestore_client()
        self.feedback_collection = self.db.collection("feedback")
        self.grievance_collection = self.db.collection("grievance_forms")

    async def create_feedback(self, feedback_data: dict) -> str:
        feedback_id = f"FB_{uuid.uuid4().hex[:8].upper()}"
        feedback_data["feedback_id"] = feedback_id
        feedback_data["created_at"] = datetime.now(timezone.utc)
        
        await self.feedback_collection.document(feedback_id).set(feedback_data)
        return feedback_id

    async def get_feedback_by_id(self, feedback_id: str) -> Optional[dict]:
        docs = self.feedback_collection.where("feedback_id", "==", feedback_id).limit(1).stream()
        async for doc in docs:
            return doc.to_dict()
        return None

    async def get_pending_feedbacks(self, citizen_id: str) -> List[dict]:
        # Get form_ids already rated by this citizen
        rated_form_ids = await self._get_rated_form_ids(citizen_id)

        # Query grievances with completed statuses for this citizen
        docs = self.grievance_collection.where("user_id", "==", citizen_id)\
                                       .where("status", "in", ["completed", "resolved", "closed"])\
                                       .stream()

        pending_grievances = []
        async for doc in docs:
            g = doc.to_dict()
            fid = g.get("form_id") or doc.id
            
            if not fid or fid in rated_form_ids:
                continue
                
            pending_grievances.append({
                "form_id": fid,
                "grievance_title": g.get("title", g.get("subject", "Unknown Title")),
                "officer_name": g.get("officer_name") or g.get("assigned_officer") or "Unknown Officer",
                "resolved_date": g.get("resolved_date", g.get("resolved_at", datetime.now(timezone.utc))).isoformat() if hasattr(g.get("resolved_date"), "isoformat") else str(g.get("resolved_date")),
                "officer_evidence_path": g.get("officer_evidence_path")
            })

        return pending_grievances

    async def _get_rated_form_ids(self, citizen_id: str) -> List[str]:
        docs = self.feedback_collection.where("citizen_id", "==", citizen_id).stream()
        form_ids = []
        async for doc in docs:
            data = doc.to_dict()
            if "form_id" in data:
                form_ids.append(data["form_id"])
        return form_ids

    async def get_officer_stats(self, officer_id: str) -> dict:
        # Use Firestore aggregation for stats if supported, or manual scan for small volumes
        query = self.feedback_collection.where("officer_id", "==", officer_id)
        
        # Total feedbacks
        count_snap = await query.count().get()
        total_feedbacks = count_snap[0].value
        
        if total_feedbacks == 0:
            return {
                "officer_id": officer_id,
                "total_feedbacks": 0,
                "average_rating": 0.0,
                "conflict_rate": 0.0,
                "escalation_rate": 0.0,
                "performance_score": 0.0
            }

        # For averages and sums, we stream and calculate since Firestore aggregation for nested fields is tricky
        docs = query.stream()
        total_overall = 0
        total_speed = 0
        total_quality = 0
        conflicts = 0
        escalations = 0
        
        async for doc in docs:
            data = doc.to_dict()
            ratings = data.get("ratings", {})
            total_overall += ratings.get("overall", 0)
            total_speed += ratings.get("speed", 0)
            total_quality += ratings.get("quality", 0)
            if data.get("conflict_detected"):
                conflicts += 1
            if data.get("escalated"):
                escalations += 1
                
        avg_overall = total_overall / total_feedbacks
        avg_speed = total_speed / total_feedbacks
        avg_quality = total_quality / total_feedbacks
        
        conflict_rate = conflicts / total_feedbacks
        escalation_rate = escalations / total_feedbacks
        avg_rating = (avg_overall + avg_speed + avg_quality) / 3
        performance_score = avg_rating * (1 - conflict_rate * 0.3 - escalation_rate * 0.2)
        
        return {
            "officer_id": officer_id,
            "total_feedbacks": total_feedbacks,
            "average_rating": round(avg_rating, 2),
            "conflict_rate": round(conflict_rate * 100, 2),
            "escalation_rate": round(escalation_rate * 100, 2),
            "performance_score": round(performance_score, 2)
        }

    async def get_grievance_details(self, form_id: str) -> Optional[dict]:
        # Try document ID first
        doc_ref = self.grievance_collection.document(form_id)
        doc = await doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if "form_id" not in data:
                data["form_id"] = doc.id
            return data
            
        # Fallback to field query
        docs = self.grievance_collection.where("form_id", "==", form_id).limit(1).stream()
        async for doc in docs:
            data = doc.to_dict()
            if "form_id" not in data:
                data["form_id"] = doc.id
            return data

        return None

    async def update_grievance_status(self, form_id: str, status: str, escalated: bool = False):
        update_data = {"status": status}
        if escalated:
            update_data["escalated"] = True
            update_data["escalation_date"] = datetime.now(timezone.utc)

        # Try update by doc ID
        try:
            await self.grievance_collection.document(form_id).update(update_data)
            logger.info(f"Updated grievance {form_id} -> {status} via doc ID")
            return
        except Exception:
            pass

        # Fallback to status update by field
        docs = self.grievance_collection.where("form_id", "==", form_id).stream()
        async for doc in docs:
            await doc.reference.update(update_data)
            logger.info(f"Updated grievance {form_id} -> {status} via field query")

feedback_db = FeedbackDatabase()

