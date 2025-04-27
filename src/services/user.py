from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.users import UserRepository
from src.schemas.user import UserCreate
from src.services.auth import AuthService


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.auth_service = AuthService(db)

    async def create_user(self, user_data: UserCreate) -> User:

        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        user = await self.user_repository.get_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        user = await self.user_repository.get_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        user = await self.user_repository.confirmed_email(email)
        return user

    async def update_avatar_url(self, email: str, url: str):
        return await self.user_repository.update_avatar_url(email, url)

    async def update_password(self, email: str, new_password: str) -> User:
        hashed_password = self.auth_service._hash_password(new_password)
        user = await self.user_repository.update_password(email, hashed_password)
        return user
