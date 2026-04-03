from .connection import user_collection
from ..models.user import UserCreate, UserResponse
from shared.utils.auth_utils import get_password_hash
from typing import List, Optional

class UserRepository:
    async def create_user(self, user: UserCreate) -> str:
        doc_ref = user_collection.document()
        # FireStore takes a dict
        await doc_ref.set(user.dict())
        return doc_ref.id

    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        doc = await user_collection.document(user_id).get()
        if doc.exists:
            user = doc.to_dict()
            return UserResponse(
                id=doc.id,
                full_name=user["full_name"],
                mobile_number=user["mobile_number"],
                residential_address=user["residential_address"],
                email=user["email"],
                language_preference=user["language_preference"]
            )
        return None

    async def get_all_users(self) -> List[UserResponse]:
        users = []
        async for doc in user_collection.stream():
            user = doc.to_dict()
            users.append(UserResponse(
                id=doc.id,
                full_name=user["full_name"],
                mobile_number=user["mobile_number"],
                residential_address=user["residential_address"],
                email=user["email"],
                language_preference=user["language_preference"]
            ))
        return users

    async def update_user(self, user_id: str, user: UserCreate) -> bool:
        # update() throws if document doesn't exist, so we ensure standard update
        try:
            await user_collection.document(user_id).update(user.dict())
            return True
        except Exception:
            return False

    async def delete_user(self, user_id: str) -> bool:
        try:
            await user_collection.document(user_id).delete()
            return True
        except Exception:
            return False

    async def create_user_with_password(self, user: UserCreate) -> str:
        hashed_password = get_password_hash(user.password)
        user_data = user.dict()
        user_data["password"] = hashed_password
        
        doc_ref = user_collection.document()
        await doc_ref.set(user_data)
        return doc_ref.id

    async def get_user_by_mobile(self, mobile_number: str) -> Optional[dict]:
        docs = user_collection.where("mobile_number", "==", mobile_number).limit(1).stream()
        async for doc in docs:
            user = doc.to_dict()
            user["_id"] = doc.id
            print(f"Fetched user by mobile: {user}")
            return user
        return None

