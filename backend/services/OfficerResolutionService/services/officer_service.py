from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from shared.firebase_client import get_firestore_client
from ..models.resolution import ResolutionRecord, TicketStatus, ClarificationRequest
from ..schemas.responses import DashboardView, TicketOverview, ClarificationsListResponse, ClarificationItem

class OfficerService:
    def __init__(self):
        self.db = get_firestore_client()
        # Firestore collections
        self.resolutions_collection = self.db.collection("resolutions")
        self.clarifications_collection = self.db.collection("clarifications")
        self.analysis_collection = self.db.collection("analysis_records")
        self.grievance_collection = self.db.collection("grievance_forms")

    async def get_officer_dashboard(self, officer_id: str) -> List[DashboardView]:
        """Get all assigned tickets for an officer by querying AI Analysis collection, excluding 'completed' status"""
        # Firestore query for assigned_officer_id and status != 'completed'
        # Note: Firestore doesn't support != directly in complex queries without an index, 
        # but we can filter 'completed' in memory if needed, or if it's just 'assigned'/'in_progress' and 'seeking_info' we can query those.
        # For now, let's stream and filter in memory for simplicity if the volume is low, or use multiple queries.
        docs = self.analysis_collection.where("assigned_officer_id", "==", officer_id).stream()
        
        dashboard_items = []
        async for doc in docs:
            record = doc.to_dict()
            if record.get("status") == "completed":
                continue
                
            # Map analysis record to ticket overview
            ticket = TicketOverview(
                grievance_id=record["form_id"],
                status=TicketStatus.ASSIGNED,  # Default to assigned in resolution context
                priority_level=record["urgency_level"],
                priority_reasoning=record["priority_reasoning"],
                cluster_info=record.get("cluster_info", {}),
                assigned_at=record["analyzed_at"],
                original_documents=record.get("document_insights", []) if record.get("document_insights") else []
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
        
        # Check if resolution record exists
        res_docs = self.resolutions_collection.where("grievance_id", "==", grievance_id).where("officer_id", "==", officer_id).limit(1).stream()
        resolution = None
        resolution_id = None
        async for doc in res_docs:
            resolution = doc.to_dict()
            resolution_id = doc.id
            break
        
        officer_name = ""
        if not resolution:
            # Pull from analysis record to initialize
            analysis_docs = self.analysis_collection.where("form_id", "==", grievance_id).limit(1).stream()
            analysis_record = None
            async for doc in analysis_docs:
                analysis_record = doc.to_dict()
                break
                
            if not analysis_record:
                raise ValueError("Ticket not found in analysis records")
            
            res_obj = ResolutionRecord(
                grievance_id=grievance_id,
                officer_id=officer_id,
                officer_name=analysis_record["assigned_officer_name"],
                status=TicketStatus.ASSIGNED,
                priority_level=analysis_record["urgency_level"],
                priority_reasoning=analysis_record["priority_reasoning"],
                assigned_at=analysis_record["analyzed_at"]
            )
            doc_ref = self.resolutions_collection.document()
            await doc_ref.set(res_obj.dict(exclude={"id"}))
            resolution_id = doc_ref.id
            officer_name = res_obj.officer_name
            resolution = res_obj.dict()
        else:
            officer_name = resolution["officer_name"]
        
        # Proceed with update
        update_data = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        # Set timestamps based on status
        if new_status == TicketStatus.IN_PROGRESS and not resolution.get("started_at"):
            update_data["started_at"] = datetime.utcnow()
        
        # Add progress update
        if progress_note:
            from google.cloud import firestore
            progress_update = {
                "timestamp": datetime.utcnow(),
                "status": new_status,
                "note": progress_note,
                "officer_id": officer_id
            }
            # Use arrayUnion for progress_updates
            await self.resolutions_collection.document(resolution_id).update({
                **update_data,
                "progress_updates": firestore.AsyncArrayUnion([progress_update])
            })
        else:
            await self.resolutions_collection.document(resolution_id).update(update_data)
        
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
        res_docs = self.resolutions_collection.where("grievance_id", "==", grievance_id).where("officer_id", "==", officer_id).limit(1).stream()
        resolution = None
        resolution_id = None
        async for doc in res_docs:
            resolution = doc.to_dict()
            resolution_id = doc.id
            break
        
        officer_name = ""
        if not resolution:
            analysis_docs = self.analysis_collection.where("form_id", "==", grievance_id).limit(1).stream()
            analysis_record = None
            async for doc in analysis_docs:
                analysis_record = doc.to_dict()
                break
                
            if not analysis_record:
                raise ValueError("Ticket not found in analysis records")
            
            res_obj = ResolutionRecord(
                grievance_id=grievance_id,
                officer_id=officer_id,
                officer_name=analysis_record["assigned_officer_name"],
                status=TicketStatus.ASSIGNED,
                priority_level=analysis_record["urgency_level"],
                priority_reasoning=analysis_record["priority_reasoning"],
                assigned_at=analysis_record["analyzed_at"]
            )
            doc_ref = self.resolutions_collection.document()
            await doc_ref.set(res_obj.dict(exclude={"id"}))
            resolution_id = doc_ref.id
            officer_name = res_obj.officer_name
        else:
            officer_name = resolution["officer_name"]
        
        # Proceed with clarification
        clarification = ClarificationRequest(
            resolution_id=resolution_id,
            grievance_id=grievance_id,
            officer_id=officer_id,
            message=message
        )
        
        # Insert clarification
        clar_ref = self.clarifications_collection.document()
        await clar_ref.set(clarification.dict(exclude={"id"}))
        
        # Update resolution status to seeking_info
        from google.cloud import firestore
        await self.resolutions_collection.document(resolution_id).update({
            "status": TicketStatus.SEEKING_INFO,
            "updated_at": datetime.utcnow(),
            "clarification_requests": firestore.AsyncArrayUnion([{
                "clarification_id": clar_ref.id,
                "message": message,
                "requested_at": clarification.requested_at
            }])
        })
        
        # TODO: Send notification to citizen via bot
        await self._send_clarification_to_citizen(grievance_id, message, officer_name)
        
        return {
            "success": True,
            "message": "Clarification request sent to citizen",
            "clarification_id": clar_ref.id,
            "sent_at": clarification.requested_at
        }

    async def resolve_ticket(self, officer_id: str, grievance_id: str, 
                           action_taken: str, closing_remark: str, resolution_photos: List[str]) -> Dict[str, Any]:
        """Mark ticket as resolved - ensure resolution record exists"""
        
        if not resolution_photos:
            raise ValueError("Resolution photos are mandatory")
        
        # Ensure resolution record exists
        res_docs = self.resolutions_collection.where("grievance_id", "==", grievance_id).where("officer_id", "==", officer_id).limit(1).stream()
        resolution = None
        resolution_id = None
        async for doc in res_docs:
            resolution = doc.to_dict()
            resolution_id = doc.id
            break
        
        officer_name = ""
        started_at = None
        if not resolution:
            analysis_docs = self.analysis_collection.where("form_id", "==", grievance_id).limit(1).stream()
            analysis_record = None
            async for doc in analysis_docs:
                analysis_record = doc.to_dict()
                break
                
            if not analysis_record:
                raise ValueError("Ticket not found in analysis records")
            
            res_obj = ResolutionRecord(
                grievance_id=grievance_id,
                officer_id=officer_id,
                officer_name=analysis_record["assigned_officer_name"],
                status=TicketStatus.ASSIGNED,
                priority_level=analysis_record["urgency_level"],
                priority_reasoning=analysis_record["priority_reasoning"],
                assigned_at=analysis_record["analyzed_at"]
            )
            doc_ref = self.resolutions_collection.document()
            await doc_ref.set(res_obj.dict(exclude={"id"}))
            resolution_id = doc_ref.id
            officer_name = res_obj.officer_name
            started_at = res_obj.assigned_at
        else:
            officer_name = resolution["officer_name"]
            started_at = resolution.get("started_at") or resolution["assigned_at"]
        
        # Proceed with resolution
        resolved_at = datetime.utcnow()
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
        completion_time = (resolved_at.replace(tzinfo=timezone.utc) - started_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600  # hours
        
        # Update resolution record
        await self.resolutions_collection.document(resolution_id).update({
            "status": TicketStatus.RESOLVED,
            "action_taken": action_taken,
            "closing_remark": closing_remark,
            "resolution_photos": resolution_photos,
            "resolved_at": resolved_at,
            "completion_time_hours": completion_time,
            "updated_at": resolved_at
        })
        
        # Update analysis_records status to "completed"
        analysis_docs = self.analysis_collection.where("form_id", "==", grievance_id).stream()
        async for doc in analysis_docs:
            await doc.reference.update({"status": "completed"})
        
        # Update grievance_forms status to "completed" and add resolution info
        grievance_docs = self.grievance_collection.where("form_id", "==", grievance_id).stream()
        async for doc in grievance_docs:
            await doc.reference.update({
                "status": "completed",
                "action_taken": action_taken,
                "closing_remark": closing_remark,
                "resolution_photos": resolution_photos,
                "resolved_at": resolved_at,
                "officer_name": officer_name
            })
        
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
        docs = self.clarifications_collection.where("officer_id", "==", officer_id).stream()
        clarifications = []
        async for doc in docs:
            data = doc.to_dict()
            clarification = ClarificationItem(
                clarification_id=doc.id,
                grievance_id=data["grievance_id"],
                officer_id=data["officer_id"],
                message=data["message"],
                requested_at=data["requested_at"],
                citizen_response=data.get("citizen_response"),
                responded_at=data.get("responded_at")
            )
            clarifications.append(clarification)
        return ClarificationsListResponse(clarifications=clarifications)

    async def get_resolved_tickets(self, officer_id: str) -> List[DashboardView]:
        """Get all resolved tickets for an officer"""
        docs = self.resolutions_collection.where("officer_id", "==", officer_id).where("status", "==", "resolved").stream()
        
        resolved_items = []
        async for doc in docs:
            record = doc.to_dict()
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
        # Firestore counting
        counts = {"assigned": 0, "in_progress": 0, "completed": 0}
        
        for status in counts.keys():
            count_query = self.analysis_collection.where("assigned_officer_id", "==", officer_id).where("status", "==", status).count()
            snapshot = await count_query.get()
            counts[status] = snapshot[0].value
            
        # Add clarifications count
        clar_count_query = self.clarifications_collection.where("officer_id", "==", officer_id).count()
        clar_snapshot = await clar_count_query.get()
        counts["clarifications"] = clar_snapshot[0].value
        
        return counts

    async def _notify_citizen_status_update(self, grievance_id: str, status: TicketStatus, officer_name: str):
        """Send status update notification to citizen"""
        print(f"Notification: Officer {officer_name} updated ticket {grievance_id} to {status}")

    async def _send_clarification_to_citizen(self, grievance_id: str, message: str, officer_name: str):
        """Send clarification request to citizen via bot"""
        print(f"Clarification from {officer_name}: {message}")

    async def _notify_citizen_resolution(self, grievance_id: str, closing_remark: str, officer_name: str):
        """Send resolution notification to citizen"""
        print(f"Resolution notification: {closing_remark}")

