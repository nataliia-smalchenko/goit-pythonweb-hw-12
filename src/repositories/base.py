"""
Base repository for database operations.

This module provides a generic base repository class that implements
common database operations for all models. It uses SQLAlchemy's async
session for database operations and provides type-safe methods for
CRUD operations.

The base repository serves as a foundation for all other repositories
in the application, ensuring consistent database access patterns.
"""

from typing import TypeVar, Type, Generic

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository for database operations.

    This class provides common database operations for any model type.
    It implements basic CRUD operations and serves as a base class
    for all other repositories in the application.

    Attributes:
        db (AsyncSession): Database session for operations
        model (Type[ModelType]): Model class for operations
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        """
        Initialize the base repository.

        Args:
            session (AsyncSession): Database session
            model (Type[ModelType]): Model class for operations
        """
        self.db = session
        self.model: Type[ModelType] = model

    async def get_all(self) -> list[ModelType]:
        """
        Get all instances of the model.

        Returns:
            list[ModelType]: List of all model instances
        """
        stmt = select(self.model)
        todos = await self.db.execute(stmt)
        return list(todos.scalars().all())

    async def get_by_id(self, _id: int) -> ModelType | None:
        """
        Get a model instance by its ID.

        Args:
            _id (int): ID of the model instance

        Returns:
            ModelType | None: Model instance if found, None otherwise
        """
        result = await self.db.execute(select(self.model).where(self.model.id == _id))
        return result.scalars().first()

    async def create(self, instance: ModelType) -> ModelType:
        """
        Create a new model instance.

        Args:
            instance (ModelType): Model instance to create

        Returns:
            ModelType: Created model instance
        """
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """
        Update an existing model instance.

        Args:
            instance (ModelType): Model instance to update

        Returns:
            ModelType: Updated model instance
        """
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """
        Delete a model instance.

        Args:
            instance (ModelType): Model instance to delete
        """
        await self.db.delete(instance)
        await self.db.commit()
