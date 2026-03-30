from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from services.superuser_services.models.staff_user import StaffUser, UserRole, Department
from services.superuser_services.db.connection import get_database
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self):
        self.db: AsyncIOMotorDatabase = None
        self.collection_name = "staff_users"
    
    def get_collection(self):
        if self.db is None:
            self.db = get_database()
        return self.db[self.collection_name]
    
    async def create_user(self, user: StaffUser) -> str:
        """Create a new user"""
        try:
            collection = self.get_collection()
            user_dict = user.model_dump(by_alias=True, exclude={"staff_id"})
            user_dict["_id"] = user.staff_id
            
            result = await collection.insert_one(user_dict)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[StaffUser]:
        """Get user by email"""
        try:
            collection = self.get_collection()
            user_doc = await collection.find_one({"email": email})
            
            if user_doc:
                user_doc["staff_id"] = user_doc.pop("_id")
                return StaffUser(**user_doc)
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise
    
    async def get_user_by_id(self, staff_id: str) -> Optional[StaffUser]:
        """Get user by staff ID"""
        try:
            collection = self.get_collection()
            user_doc = await collection.find_one({"_id": staff_id})
            
            if user_doc:
                user_doc["staff_id"] = user_doc.pop("_id")
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
            
            result = await collection.update_one(
                {"_id": staff_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise
    
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
            
            # Build filter query
            filter_query = {}
            if dept:
                filter_query["metadata.dept"] = dept
            if ward:
                filter_query["metadata.ward"] = ward
            if role:
                filter_query["role"] = role
            
            # Get total count
            total_count = await collection.count_documents(filter_query)
            
            # Get paginated results
            skip = (page - 1) * page_size
            cursor = collection.find(filter_query).skip(skip).limit(page_size)
            
            users = []
            async for user_doc in cursor:
                user_doc["staff_id"] = user_doc.pop("_id")
                users.append(StaffUser(**user_doc))
            
            return users, total_count
        except Exception as e:
            logger.error(f"Error getting filtered users: {e}")
            raise
    
    async def check_employee_id_exists(self, employee_id: str) -> bool:
        """Check if employee ID already exists"""
        try:
            collection = self.get_collection()
            result = await collection.find_one({"employee_id": employee_id})
            return result is not None
        except Exception as e:
            logger.error(f"Error checking employee ID: {e}")
            raise

user_repository = UserRepository()
