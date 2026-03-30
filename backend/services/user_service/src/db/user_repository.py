from .connection import user_collection
from ..models.user import UserCreate, UserResponse
from shared.utils.auth_utils import get_password_hash
from bson import ObjectId
from typing import List, Optional

class UserRepository:
    async def create_user(self, user: UserCreate) -> str:
        result = await user_collection.insert_one(user.dict())
        return str(result.inserted_id)

    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        user = await user_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return UserResponse(
                id=str(user["_id"]),
                full_name=user["full_name"],
                mobile_number=user["mobile_number"],
                residential_address=user["residential_address"],
                email=user["email"],
                language_preference=user["language_preference"]
            )
        return None

    async def get_all_users(self) -> List[UserResponse]:
        users = []
        async for user in user_collection.find():
            users.append(UserResponse(
                id=str(user["_id"]),
                full_name=user["full_name"],
                mobile_number=user["mobile_number"],
                residential_address=user["residential_address"],
                email=user["email"],
                language_preference=user["language_preference"]
            ))
        return users

    async def update_user(self, user_id: str, user: UserCreate) -> bool:
        result = await user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": user.dict()})
        return result.modified_count > 0

    async def delete_user(self, user_id: str) -> bool:
        result = await user_collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    async def create_user_with_password(self, user: UserCreate) -> str:
        hashed_password = get_password_hash(user.password)
        user_data = user.dict()
        user_data["password"] = hashed_password
        result = await user_collection.insert_one(user_data)
        return str(result.inserted_id)

    async def get_user_by_mobile(self, mobile_number: str) -> Optional[dict]:
        user = await user_collection.find_one({"mobile_number": mobile_number})
        print(f"Fetched user by mobile: {user}")
        return user
