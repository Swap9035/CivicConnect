from ..db.user_repository import UserRepository
from ..models.user import UserCreate, UserResponse, UserLogin, Token
from shared.utils.auth_utils import verify_password, create_access_token
from typing import List, Optional

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    async def create_user(self, user: UserCreate) -> str:
        return await self.repository.create_user(user)

    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        return await self.repository.get_user(user_id)

    async def get_all_users(self) -> List[UserResponse]:
        return await self.repository.get_all_users()

    async def update_user(self, user_id: str, user: UserCreate) -> bool:
        return await self.repository.update_user(user_id, user)

    async def delete_user(self, user_id: str) -> bool:
        return await self.repository.delete_user(user_id)

    async def signup(self, user: UserCreate) -> str:
        # Check if user exists
        existing = await self.repository.get_user_by_mobile(user.mobile_number)
        if existing:
            raise ValueError("User already exists")
        return await self.repository.create_user_with_password(user)

    async def login(self, user: UserLogin) -> Token:
        db_user = await self.repository.get_user_by_mobile(user.mobile_number)
        print(f"DB User: {db_user}")
        if not db_user or not verify_password(user.password, db_user["password"]):
            raise ValueError("Invalid credentials")
        access_token = create_access_token(data={"sub": user.mobile_number})
        return Token(access_token=access_token)
