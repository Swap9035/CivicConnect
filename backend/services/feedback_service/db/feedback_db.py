from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import List, Optional
import os
from bson import ObjectId
import uuid
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()  # Load environment variables

logger = logging.getLogger(__name__)

class FeedbackDatabase:
    def __init__(self):
        self.mongo_url = os.getenv("MONGO_URI")
        self.client = AsyncIOMotorClient(self.mongo_url)
        self.db = self.client.feedback_db
        self.feedback_collection = self.db.feedback
        
        # References to other databases
        self.grievance_db = self.client.grievance_db
        self.users_db = self.client.user_db
        self.superuser_db = self.client.superuserdb

    async def create_feedback(self, feedback_data: dict) -> str:
        feedback_data["feedback_id"] = f"FB_{uuid.uuid4().hex[:8].upper()}"
        feedback_data["created_at"] = datetime.utcnow()
        
        result = await self.feedback_collection.insert_one(feedback_data)
        return feedback_data["feedback_id"]

    async def get_feedback_by_id(self, feedback_id: str) -> Optional[dict]:
        return await self.feedback_collection.find_one({"feedback_id": feedback_id})

    async def get_pending_feedbacks(self, citizen_id: str) -> List[dict]:
        # Get form_ids already rated by this citizen
        rated_form_ids = await self._get_rated_form_ids(citizen_id)

        # Accept several "completed" statuses and query both collections
        query = {
            "user_id": citizen_id,
            "status": {"$in": ["completed", "resolved", "closed"]}
        }

        # Fetch from both possible collections (guard against missing collections)
        grievances1 = []
        grievances2 = []
        coll1 = getattr(self.grievance_db, "grievance_forms", None)
        if coll1 is not None:
            cursor1 = coll1.find(query)
            grievances1 = await cursor1.to_list(length=None)
        coll2 = getattr(self.grievance_db, "grievances", None)
        if coll2 is not None:
            cursor2 = coll2.find(query)
            grievances2 = await cursor2.to_list(length=None)

        all_grievances = grievances1 + grievances2

        # Helper to extract form id safely
        def _get_form_id(g):
            return (
                g.get("form_id") or
                g.get("formId") or
                (str(g.get("_id")) if g.get("_id") is not None else None) or
                g.get("id") or
                g.get("ticket_id") or
                g.get("ticketId")
            )

        # Filter out already rated grievances and build response
        pending_grievances = []
        for g in all_grievances:
            fid = _get_form_id(g)
            if not fid:
                continue
            if fid in rated_form_ids:
                continue
            pending_grievances.append({
                "form_id": fid,
                "grievance_title": g.get("title", g.get("subject", "Unknown Title")),
                "officer_name": g.get("officer_name") or g.get("assigned_officer") or "Unknown Officer",
                "resolved_date": g.get("resolved_date", g.get("resolved_at", datetime.utcnow())).isoformat(),
                "officer_evidence_path": g.get("officer_evidence_path")
            })

        return pending_grievances

    async def _get_rated_form_ids(self, citizen_id: str) -> List[str]:
        cursor = self.feedback_collection.find(
            {"citizen_id": citizen_id}, 
            {"form_id": 1, "_id": 0}
        )
        feedbacks = await cursor.to_list(length=None)
        return [f["form_id"] for f in feedbacks]

    async def get_officer_stats(self, officer_id: str) -> dict:
        pipeline = [
            {"$match": {"officer_id": officer_id}},
            {
                "$group": {
                    "_id": "$officer_id",
                    "total_feedbacks": {"$sum": 1},
                    "avg_overall": {"$avg": "$ratings.overall"},
                    "avg_speed": {"$avg": "$ratings.speed"},
                    "avg_quality": {"$avg": "$ratings.quality"},
                    "conflicts": {"$sum": {"$cond": ["$conflict_detected", 1, 0]}},
                    "escalations": {"$sum": {"$cond": ["$escalated", 1, 0]}}
                }
            }
        ]
        
        cursor = self.feedback_collection.aggregate(pipeline)
        stats = await cursor.to_list(length=1)
        
        if not stats:
            return {
                "officer_id": officer_id,
                "total_feedbacks": 0,
                "average_rating": 0.0,
                "conflict_rate": 0.0,
                "escalation_rate": 0.0,
                "performance_score": 0.0
            }
        
        stat = stats[0]
        conflict_rate = stat["conflicts"] / stat["total_feedbacks"] if stat["total_feedbacks"] > 0 else 0
        escalation_rate = stat["escalations"] / stat["total_feedbacks"] if stat["total_feedbacks"] > 0 else 0
        avg_rating = (stat["avg_overall"] + stat["avg_speed"] + stat["avg_quality"]) / 3
        performance_score = avg_rating * (1 - conflict_rate * 0.3 - escalation_rate * 0.2)
        
        return {
            "officer_id": officer_id,
            "total_feedbacks": stat["total_feedbacks"],
            "average_rating": round(avg_rating, 2),
            "conflict_rate": round(conflict_rate * 100, 2),
            "escalation_rate": round(escalation_rate * 100, 2),
            "performance_score": round(performance_score, 2)
        }

    async def get_grievance_details(self, form_id: str) -> Optional[dict]:
        """
        Robustly search multiple collections and id fields to find a grievance document.
        """
        # Build OR conditions for multiple id fields
        or_clauses = [
            {"form_id": form_id},
            {"formId": form_id},
            {"id": form_id},
            {"ticket_id": form_id},
            {"ticketId": form_id},
        ]
        # Add _id lookup if form_id looks like an ObjectId
        try:
            if ObjectId.is_valid(form_id):
                or_clauses.append({"_id": ObjectId(form_id)})
        except Exception:
            pass

        query = {"$or": or_clauses}

        # Try common collections
        for coll_name in ("grievances", "grievance_forms"):
            coll = getattr(self.grievance_db, coll_name, None)
            if coll is None:
                continue
            doc = await coll.find_one(query)
            if doc:
                # normalize common fields for downstream code
                if "form_id" not in doc:
                    doc["form_id"] = (
                        doc.get("formId") or doc.get("id") or str(doc.get("_id"))
                    )
                return doc

        logger.debug(f"Grievance not found for id {form_id}")
        return None

    async def update_grievance_status(self, form_id: str, status: str, escalated: bool = False):
        update_data = {"status": status}
        if escalated:
            update_data["escalated"] = True
            update_data["escalation_date"] = datetime.utcnow()

        updated = False
        # Try to update across both collections and mark if any updated
        for coll_name in ("grievances", "grievance_forms"):
            coll = getattr(self.grievance_db, coll_name, None)
            if coll is None:
                continue
            result = await coll.update_one({"form_id": form_id}, {"$set": update_data})
            if result.modified_count and result.modified_count > 0:
                updated = True
                logger.info(f"Updated {coll_name} for {form_id} -> {status}")

        if not updated:
            # Fallback: try matching other id fields (_id or id etc.)
            or_clauses = [
                {"formId": form_id},
                {"id": form_id},
                {"ticket_id": form_id},
                {"ticketId": form_id},
            ]
            try:
                if ObjectId.is_valid(form_id):
                    or_clauses.append({"_id": ObjectId(form_id)})
            except Exception:
                pass
            query = {"$or": or_clauses}
            for coll_name in ("grievances", "grievance_forms"):
                coll = getattr(self.grievance_db, coll_name, None)
                if coll is None:
                    continue
                result = await coll.update_one(query, {"$set": update_data})
                if result.modified_count and result.modified_count > 0:
                    updated = True
                    logger.info(f"Updated {coll_name} (fallback) for {form_id} -> {status}")

        if not updated:
            logger.warning(f"Unable to update grievance status for {form_id}. No matching documents found.")

feedback_db = FeedbackDatabase()
