from typing import Optional, List, Dict, Any
from google.cloud.firestore_v1.async_client import AsyncClient
from services.superuser_services.models.staff_user import StaffUser, UserRole, Department
from services.superuser_services.db.connection import get_database
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self):
        self.db: AsyncClient = None
        self.collection_name = "staff_users"
    
    def get_collection(self):
        if self.db is None:
            self.db = get_database()
        return self.db.collection(self.collection_name)
    
    async def create_user(self, user: StaffUser) -> str:
        """Create a new user"""
        try:
            collection = self.get_collection()
            user_dict = user.model_dump(by_alias=True, exclude={"staff_id"})
            
            # Use staff_id as the document ID if provided, otherwise auto-generate
            doc_ref = collection.document(user.staff_id)
            await doc_ref.set(user_dict)
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[StaffUser]:
        """Get user by email"""
        try:
            collection = self.get_collection()
            docs = collection.where("email", "==", email).limit(1).stream()
            async for doc in docs:
                user_doc = doc.to_dict()
                user_doc["staff_id"] = doc.id
                return StaffUser(**user_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise
    
    async def get_user_by_id(self, staff_id: str) -> Optional[StaffUser]:
        """Get user by staff ID"""
        try:
            collection = self.get_collection()
            doc = await collection.document(staff_id).get()
            
            if doc.exists:
                user_doc = doc.to_dict()
                user_doc["staff_id"] = doc.id
                return StaffUser(**user_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            raise
    
    async def update_user(self, staff_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            collection = self.get_collection()
            update_data["updated_at"] = datetime.utcnow()
            
            await collection.document(staff_id).update(update_data)
            return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False  # Or raise depending on previous behavior, previously returned False if modified_count > 0 didn't hit but it threw on real error
    
    async def get_users_by_filters(
        self, 
        dept: Optional[Department] = None,
        ward: Optional[str] = None,
        role: Optional[UserRole] = None,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[List[StaffUser], int]:
        """Get users with filters and pagination"""
        try:
            collection = self.get_collection()
            
            query = collection
            if dept:
                query = query.where("metadata.dept", "==", dept)
            if ward:
                query = query.where("metadata.ward", "==", ward)
            if role:
                query = query.where("role", "==", role)
            
            # Get total count
            count_query = query.count()
            count_snapshot = await count_query.get()
            total_count = count_snapshot[0].value
            
            # Get paginated results
            skip = (page - 1) * page_size
            cursor = query.offset(skip).limit(page_size).stream()
            
            users = []
            async for doc in cursor:
                user_doc = doc.to_dict()
                user_doc["staff_id"] = doc.id
                users.append(StaffUser(**user_doc))
            
            return users, total_count
        except Exception as e:
            logger.error(f"Error getting filtered users: {e}")
            raise
    
    async def check_employee_id_exists(self, employee_id: str) -> bool:
        """Check if employee ID already exists"""
        try:
            collection = self.get_collection()
            docs = collection.where("employee_id", "==", employee_id).limit(1).stream()
            async for doc in docs:
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking employee ID: {e}")
            raise

user_repository = UserRepository()

