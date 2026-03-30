from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from ..config.database import officer_resolution_db
from ..models.resolution import ResolutionRecord, TicketStatus, ClarificationRequest
from ..schemas.responses import DashboardView, TicketOverview, ClarificationsListResponse, ClarificationItem

class OfficerService:
    def __init__(self):
        self.db = officer_resolution_db.database
        self.ai_db = officer_resolution_db.ai_database  # AI Analysis DB
        # Add grievance DB connection (assuming it's accessible)
        from ...AIFormFilling.src.db.connection import get_grievance_collection
        self.grievance_collection = get_grievance_collection()  # Assuming this function exists
        self.resolutions_collection = self.db.resolutions
        self.clarifications_collection = self.db.clarifications
        self.analysis_collection = self.ai_db.analysis_records  # Analysis records

    async def get_officer_dashboard(self, officer_id: str) -> List[DashboardView]:
        """Get all assigned tickets for an officer by querying AI Analysis DB, excluding 'completed' status"""
        cursor = self.analysis_collection.find({
            "assigned_officer_id": officer_id,
            "status": {"$ne": "completed"}  # Exclude completed tickets
        })
        
        dashboard_items = []
        async for record in cursor:
            # Map analysis record to ticket overview
            ticket = TicketOverview(
                grievance_id=record["form_id"],
                status=TicketStatus.ASSIGNED,  # Default to assigned in resolution context
                priority_level=record["urgency_level"],
                priority_reasoning=record["priority_reasoning"],
                cluster_info=record.get("cluster_info", {}),  # Assuming cluster_info might be added later
                assigned_at=record["analyzed_at"],
                original_documents=record.get("document_insights", []) if record.get("document_insights") else []  # Placeholder for media
            )
            
            # Format urgency banner
            urgency_banner = f"{ticket.priority_level.upper()}"
            if ticket.priority_level == "critical":
                urgency_banner = f"🔴 {urgency_banner}"
            elif ticket.priority_level == "high":
                urgency_banner = f"🟡 {urgency_banner}"
            
            # Format context panel
            context_panel = ticket.priority_reasoning
            
            # Format cluster summary (indicates if linked to cluster of similar requests)
            cluster_summary = "Individual complaint"
            if record.get("status") == "Linked":
                parent_id = record.get("parent_form_id", "original")
                similarity = record.get("similarity_score", 0)
                cluster_summary = f"Linked to cluster (parent: {parent_id}, similarity: {similarity:.2f}) - helps identify similar requests"
            
            dashboard_view = DashboardView(
                ticket=ticket,
                urgency_banner=urgency_banner,
                context_panel=context_panel,
                cluster_summary=cluster_summary,
                media_gallery=ticket.original_documents
            )
            dashboard_items.append(dashboard_view)
        
        return dashboard_items

    async def update_ticket_status(self, officer_id: str, grievance_id: str, 
                                 new_status: TicketStatus, progress_note: Optional[str] = None) -> Dict[str, Any]:
        """Update ticket status and log progress - create resolution record if not exists"""
        
        # Check if resolution record exists, else create from analysis record
        resolution = await self.resolutions_collection.find_one({
            "grievance_id": grievance_id,
            "officer_id": officer_id
        })
        
        if not resolution:
            # Pull from analysis record to initialize
            analysis_record = await self.analysis_collection.find_one({"form_id": grievance_id})
            if not analysis_record:
                raise ValueError("Ticket not found in analysis records")
            
            resolution = ResolutionRecord(
                grievance_id=grievance_id,
                officer_id=officer_id,
                officer_name=analysis_record["assigned_officer_name"],
                status=TicketStatus.ASSIGNED,
                priority_level=analysis_record["urgency_level"],
                priority_reasoning=analysis_record["priority_reasoning"],
                assigned_at=analysis_record["analyzed_at"]
            )
            result = await self.resolutions_collection.insert_one(resolution.dict(exclude={"id"}))
            resolution.id = str(result.inserted_id)  # Use field name for model
            resolution_id = resolution.id
            officer_name = resolution.officer_name
        else:
            resolution_id = resolution["_id"]
            officer_name = resolution["officer_name"]
        
        # Proceed with update as before
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        # Set timestamps based on status
        if new_status == TicketStatus.IN_PROGRESS and not resolution.get("started_at"):
            update_data["started_at"] = datetime.utcnow()
        
        # Add progress update
        if progress_note:
            progress_update = {
                "timestamp": datetime.utcnow(),
                "status": new_status,
                "note": progress_note,
                "officer_id": officer_id
            }
            update_data["$push"] = {"progress_updates": progress_update}
        
        # Update the record
        await self.resolutions_collection.update_one(
            {"_id": ObjectId(resolution_id)},
            {"$set": update_data} if not progress_note else {"$set": {k: v for k, v in update_data.items() if k != "$push"}, **update_data}
        )
        
        # TODO: Send notification to citizen
        await self._notify_citizen_status_update(grievance_id, new_status, officer_name=officer_name)
        
        return {
            "success": True,
            "message": f"Status updated to {new_status}",
            "new_status": new_status,
            "updated_at": update_data["updated_at"]
        }

    async def request_clarification(self, officer_id: str, grievance_id: str, message: str) -> Dict[str, Any]:
        """Send clarification request to citizen - ensure resolution record exists"""
        
        # Ensure resolution record exists (create if not)
        resolution = await self.resolutions_collection.find_one({
            "grievance_id": grievance_id,
            "officer_id": officer_id
        })
        
        if not resolution:
            analysis_record = await self.analysis_collection.find_one({"form_id": grievance_id})
            if not analysis_record:
                raise ValueError("Ticket not found in analysis records")
            
            resolution = ResolutionRecord(
                grievance_id=grievance_id,
                officer_id=officer_id,
                officer_name=analysis_record["assigned_officer_name"],
                status=TicketStatus.ASSIGNED,
                priority_level=analysis_record["urgency_level"],
                priority_reasoning=analysis_record["priority_reasoning"],
                assigned_at=analysis_record["analyzed_at"]
            )
            result = await self.resolutions_collection.insert_one(resolution.dict(exclude={"id"}))
            resolution.id = str(result.inserted_id)  # Use field name for model
            resolution_id = resolution.id
            officer_name = resolution.officer_name
        else:
            resolution_id = str(resolution["_id"])  # Convert ObjectId to string
            officer_name = resolution["officer_name"]
        
        # Proceed as before
        clarification = ClarificationRequest(
            resolution_id=resolution_id,
            grievance_id=grievance_id,
            officer_id=officer_id,
            message=message
        )
        
        # Insert clarification
        result = await self.clarifications_collection.insert_one(clarification.dict(exclude={"id"}))
        
        # Update resolution status to seeking_info
        await self.resolutions_collection.update_one(
            {"_id": ObjectId(resolution_id)},
            {
                "$set": {
                    "status": TicketStatus.SEEKING_INFO,
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "clarification_requests": {
                        "clarification_id": str(result.inserted_id),
                        "message": message,
                        "requested_at": clarification.requested_at
                    }
                }
            }
        )
        
        # TODO: Send notification to citizen via bot
        await self._send_clarification_to_citizen(grievance_id, message, officer_name)
        
        return {
            "success": True,
            "message": "Clarification request sent to citizen",
            "clarification_id": str(result.inserted_id),
            "sent_at": clarification.requested_at
        }

    async def resolve_ticket(self, officer_id: str, grievance_id: str, 
                           action_taken: str, closing_remark: str, resolution_photos: List[str]) -> Dict[str, Any]:
        """Mark ticket as resolved - ensure resolution record exists"""
        
        if not resolution_photos:
            raise ValueError("Resolution photos are mandatory")
        
        # Ensure resolution record exists
        resolution = await self.resolutions_collection.find_one({
            "grievance_id": grievance_id,
            "officer_id": officer_id
        })
        
        if not resolution:
            analysis_record = await self.analysis_collection.find_one({"form_id": grievance_id})
            if not analysis_record:
                raise ValueError("Ticket not found in analysis records")
            
            resolution = ResolutionRecord(
                grievance_id=grievance_id,
                officer_id=officer_id,
                officer_name=analysis_record["assigned_officer_name"],
                status=TicketStatus.ASSIGNED,
                priority_level=analysis_record["urgency_level"],
                priority_reasoning=analysis_record["priority_reasoning"],
                assigned_at=analysis_record["analyzed_at"]
            )
            result = await self.resolutions_collection.insert_one(resolution.dict(exclude={"id"}))
            resolution.id = str(result.inserted_id)  # Use field name for model
            resolution_id = resolution.id
            officer_name = resolution.officer_name
            started_at = resolution.assigned_at  # Default for new
        else:
            resolution_id = str(resolution["_id"])
            officer_name = resolution["officer_name"]
            started_at = resolution.get("started_at") or resolution["assigned_at"]  # Ensure not None
        
        # Proceed with resolution as before
        resolved_at = datetime.utcnow()
        completion_time = (resolved_at - started_at).total_seconds() / 3600  # hours
        
        # Update resolution record
        await self.resolutions_collection.update_one(
            {"_id": ObjectId(resolution_id)},
            {
                "$set": {
                    "status": TicketStatus.RESOLVED,
                    "action_taken": action_taken,
                    "closing_remark": closing_remark,
                    "resolution_photos": resolution_photos,
                    "resolved_at": resolved_at,
                    "completion_time_hours": completion_time,
                    "updated_at": resolved_at
                }
            }
        )
        
        # Update analysis_records status to "completed"
        await self.analysis_collection.update_one(
            {"form_id": grievance_id},
            {"$set": {"status": "completed"}}
        )
        
        # Update grievance_forms status to "completed" and add resolution info
        await self.grievance_collection.update_one(
            {"form_id": grievance_id},  # Use "form_id" to match analysis_records
            {
                "$set": {
                    "status": "completed",
                    "action_taken": action_taken,
                    "closing_remark": closing_remark,
                    "resolution_photos": resolution_photos,
                    "resolved_at": resolved_at,
                    "officer_name": officer_name
                }
            }
        )
        
        # TODO: Send resolution notification to citizen
        await self._notify_citizen_resolution(grievance_id, closing_remark, officer_name)
        
        return {
            "success": True,
            "message": "Ticket resolved successfully",
            "resolved_at": resolved_at,
            "completion_time_hours": completion_time
        }

    async def get_clarifications(self, officer_id: str) -> ClarificationsListResponse:
        """Get all clarifications requested by the officer"""
        cursor = self.clarifications_collection.find({"officer_id": officer_id})
        clarifications = []
        async for doc in cursor:
            clarification = ClarificationItem(
                clarification_id=str(doc["_id"]),
                grievance_id=doc["grievance_id"],
                officer_id=doc["officer_id"],
                message=doc["message"],
                requested_at=doc["requested_at"],
                citizen_response=doc.get("citizen_response"),
                responded_at=doc.get("responded_at")
            )
            clarifications.append(clarification)
        return ClarificationsListResponse(clarifications=clarifications)

    async def get_resolved_tickets(self, officer_id: str) -> List[DashboardView]:
        """Get all resolved tickets for an officer"""
        cursor = self.resolutions_collection.find({
            "officer_id": officer_id,
            "status": "resolved"
        })
        
        resolved_items = []
        async for record in cursor:
            # Map resolution record to ticket overview
            ticket = TicketOverview(
                grievance_id=record["grievance_id"],
                status=TicketStatus.RESOLVED,
                priority_level=record["priority_level"],
                priority_reasoning=record["priority_reasoning"],
                cluster_info=record.get("cluster_info", {}),
                assigned_at=record["assigned_at"],
                started_at=record.get("started_at"),
                resolved_at=record.get("resolved_at"),
                original_documents=record.get("original_documents", [])
            )
            
            # Format urgency banner
            urgency_banner = f"{ticket.priority_level.upper()}"
            if ticket.priority_level == "critical":
                urgency_banner = f"🔴 {urgency_banner}"
            elif ticket.priority_level == "high":
                urgency_banner = f"🟡 {urgency_banner}"
            
            # Format context panel
            context_panel = ticket.priority_reasoning
            
            # Format cluster summary
            cluster_summary = "Resolved issue"
            
            dashboard_view = DashboardView(
                ticket=ticket,
                urgency_banner=urgency_banner,
                context_panel=context_panel,
                cluster_summary=cluster_summary,
                media_gallery=record.get("resolution_photos", [])
            )
            resolved_items.append(dashboard_view)
        
        return resolved_items

    async def get_ticket_counts(self, officer_id: str) -> Dict[str, int]:
        """Get counts of tickets by status for the officer"""
        pipeline = [
            {"$match": {"assigned_officer_id": officer_id}},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        cursor = self.analysis_collection.aggregate(pipeline)
        counts = {"assigned": 0, "in_progress": 0, "completed": 0}  # Removed "resolved" as it's same as "completed"
        async for doc in cursor:
            status = doc["_id"]
            if status in counts:
                counts[status] = doc["count"]
        
        # Add clarifications count
        clarifications_count = await self.clarifications_collection.count_documents({"officer_id": officer_id})
        counts["clarifications"] = clarifications_count
        
        return counts

    async def _notify_citizen_status_update(self, grievance_id: str, status: TicketStatus, officer_name: str):
        """Send status update notification to citizen"""
        # TODO: Integrate with notification service or bot
        print(f"Notification: Officer {officer_name} updated ticket {grievance_id} to {status}")

    async def _send_clarification_to_citizen(self, grievance_id: str, message: str, officer_name: str):
        """Send clarification request to citizen via bot"""
        # TODO: Integrate with bot service
        print(f"Clarification from {officer_name}: {message}")

    async def _notify_citizen_resolution(self, grievance_id: str, closing_remark: str, officer_name: str):
        """Send resolution notification to citizen"""
        # TODO: Integrate with notification service
        print(f"Resolution notification: {closing_remark}")
