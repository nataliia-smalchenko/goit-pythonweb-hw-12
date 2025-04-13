import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repositories.base import BaseRepository
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Отримати користувача за електронною адресою."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Отримати користувача за username."""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_user(
        self, user_data: UserCreate, hashed_password: str, avatar: str
    ) -> User:
        user = User(
            **user_data.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=hashed_password,
            avatar_url=avatar,
        )
        return await self.create(user)

    async def confirmed_email(self, email: str) -> None:
        user = await self.get_by_email(email)
        user.is_verified = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        user = await self.get_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user
