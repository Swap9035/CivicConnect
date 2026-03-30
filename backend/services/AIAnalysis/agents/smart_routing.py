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
            collection = db.staff_users

            # Build base query
            query = {
                "role": "NODAL_OFFICER",
                "metadata.dept": department
            }

            # Add fuzzy ward match if provided (case-insensitive partial match)
            if area_ward_name and area_ward_name.strip():
                ward_term = area_ward_name.strip()
                ward_regex = {"$regex": f".*{re.escape(ward_term)}.*", "$options": "i"}
                query["metadata.ward"] = ward_regex

            # Query for nodal officer with matching dept and (fuzzy) ward
            officer_doc = await collection.find_one(query)

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
