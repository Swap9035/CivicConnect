import httpx
import re
import logging
from typing import Dict, Optional
from services.AIAnalysis.shared.schemas import GrievanceData, RoutingResult
from services.AIAnalysis.utils.config import settings
from services.superuser_services.db.connection import get_database as get_superuser_db

logger = logging.getLogger(__name__)

class SmartRoutingAgent:
    def __init__(self):
        
        # Department mapping
        self.department_mapping = {
            "Electricity": "Electricity",
            "Water Supply": "Water Supply",
            "Roads": "Roads",
            "Sanitation": "Sanitation",
            "Street Lights": "Street Lights",
            "Drainage": "Drainage",
            "Public Safety": "Public Safety",
            "Parks": "Parks",
            "Buildings": "Buildings"
        }
        
        # Estimated response times by urgency
        self.response_times = {
            "critical": "2 hours",
            "high": "12 hours",
            "medium": "24 hours",
            "low": "48 hours"
        }
    
    async def route_grievance(
        self, 
        grievance: GrievanceData, 
        urgency_level: str
    ) -> RoutingResult:
        """
        Route grievance to appropriate department and officer
        """
        # Get department from category
        department = self.department_mapping.get(
            grievance.category, 
            "General Administration"
        )
        
        # Find nodal officer for this department and area
        officer = await self._find_nodal_officer(
            department=department,
            area_ward_name=grievance.area_ward_name
        )
        
        # Get estimated response time
        eta = self.response_times.get(urgency_level, "48 hours")
        
        return RoutingResult(
            department=department,
            officer_id=officer["officer_id"],
            officer_name=officer["officer_name"],
            estimated_response_time=eta
        )
    
    async def _find_nodal_officer(
        self, 
        department: str, 
        area_ward_name: str
    ) -> Dict[str, str]:
        """
        Query SuperUser DB staff_users collection to find the nodal officer.
        Uses fuzzy (partial, case-insensitive) matching on ward name.
        """
        try:
            db = get_superuser_db()  # Synchronous call
            collection = db.collection("staff_users")

            # In Firestore, we query by role and dept, then filter ward in memory
            docs = collection.where("role", "==", "NODAL_OFFICER").where("metadata.dept", "==", department).stream()
            
            ward_term = (area_ward_name or "").strip().lower()
            officer_doc = None
            
            async for doc in docs:
                data = doc.to_dict()
                ward = data.get("metadata", {}).get("ward", "").lower()
                if not ward_term or ward_term in ward:
                    officer_doc = data
                    officer_doc["_id"] = doc.id
                    break

            if officer_doc:
                return {
                    "officer_id": str(officer_doc.get("_id", "DEFAULT_OFFICER")),
                    "officer_name": officer_doc.get("full_name", f"{department} - Nodal Officer")
                }
        except Exception as e:
            logger.exception("Error finding nodal officer in DB: %s", e)
        
        # Fallback to default officer
        return {
            "officer_id": "DEFAULT_OFFICER",
            "officer_name": f"{department} - Nodal Officer"
        }
