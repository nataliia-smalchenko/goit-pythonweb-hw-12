import logging
from typing import Sequence, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError  # Додано для обробки помилок БД

from src.core.depend_service import get_current_user
from src.database.db import get_db
from src.entity.models import User
from src.services.contacts import ContactService
from src.schemas.contact import (
    ContactResponseSchema,
    ContactCreateSchema,
    ContactUpdateSchema,
)

router = APIRouter(prefix="/contacts", tags=["contacts"])
logger = logging.getLogger("uvicorn.error")


@router.get("/", response_model=Sequence[ContactResponseSchema])
async def get_contacts(
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Отримати список контактів з пагінацією.
    """
    logger.info("Отримання списку контактів. Limit: %d, Offset: %d", limit, offset)
    contact_service = ContactService(db)
    contacts = await contact_service.get_contacts(
        user_id=user.id, limit=limit, offset=offset
    )
    logger.info("Отримано %d контактів", len(contacts))
    return contacts


@router.get("/search", response_model=Sequence[ContactResponseSchema])
async def search_contacts(
    first_name: Optional[str] = Query(None, description="Пошук за ім'ям"),
    last_name: Optional[str] = Query(None, description="Пошук за прізвищем"),
    email: Optional[str] = Query(None, description="Пошук за електронною адресою"),
    limit: int = Query(10, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Пошук контактів за іменем, прізвищем або електронною адресою.
    """
    logger.info(
        "Пошук контактів за параметрами: first_name=%s, last_name=%s, email=%s, limit=%d, offset=%d",
        first_name,
        last_name,
        email,
        limit,
        offset,
    )
    contact_service = ContactService(db)
    results = await contact_service.search_contacts(
        first_name=first_name,
        last_name=last_name,
        email=email,
        limit=limit,
        offset=offset,
        user_id=user.id,
    )
    logger.info("Пошук повернув %d контактів", len(results))
    return results


@router.get("/upcoming_birthdays", response_model=Sequence[ContactResponseSchema])
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Отримати контакти з днями народження, що настануть протягом наступних 7 днів.
    """
    logger.info("Отримання контактів з наближенням дня народження протягом 7 днів")
    contact_service = ContactService(db)
    contacts = await contact_service.get_contacts_with_upcoming_birthdays(user.id)
    logger.info("Знайдено %d контактів з майбутнім днем народження", len(contacts))
    return contacts


@router.get(
    "/{contact_id}",
    response_model=ContactResponseSchema,
    name="Get contact by id",
    description="Отримання контакту за ідентифікатором",
    response_description="Детальна інформація контакту",
)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Отримати контакт за його ідентифікатором.
    """
    logger.info("Спроба отримати контакт з id: %d", contact_id)
    contact_service = ContactService(db)
    contact = await contact_service.get_contact_by_id(contact_id, user.id)
    if not contact:
        logger.error("Контакт з id %d не знайдено", contact_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    logger.info("Контакт з id %d успішно отримано", contact_id)
    return contact


@router.post(
    "/",
    response_model=ContactResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_contact(
    body: ContactCreateSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Створити новий контакт.
    """
    try:
        logger.info("Створення нового контакту з даними: %s", body.model_dump())
        contact_service = ContactService(db)
        contact = await contact_service.create_contact(body, user.id)
        logger.info("Новий контакт створено з id: %d", contact.id)
        return contact
    except ValueError as e:
        logger.error("Помилка при створенні контакту: %s", str(e))
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Невалідні дані контакту: {str(e)}",
        )
    except IntegrityError as e:
        # Обробка помилок, пов'язаних з унікальними обмеженнями в БД
        logger.error("Помилка при створенні контакту: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Контакт з таким email або телефоном вже існує",
        )
    except Exception as e:
        logger.error("Неочікувана помилка при створенні контакту: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося створити контакт. Спробуйте ще раз.",
        )


@router.put("/{contact_id}", response_model=ContactResponseSchema)
async def update_contact(
    contact_id: int,
    body: ContactUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Оновити дані існуючого контакту.
    """
    try:
        logger.info(
            "Оновлення контакту з id: %d. Дані для оновлення: %s",
            contact_id,
            body.model_dump(exclude_unset=True),
        )
        contact_service = ContactService(db)
        contact = await contact_service.update_contact(contact_id, body, user.id)
        if not contact:
            logger.error(
                "Не вдалося оновити контакт. Контакт з id %d не знайдено", contact_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
            )
        logger.info("Контакт з id %d успішно оновлено", contact_id)
        return contact
    except ValueError as e:
        logger.error("Помилка при створенні контакту: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Невалідні дані контакту: {str(e)}",
        )
    except IntegrityError as e:
        logger.error("Помилка при оновленні контакту: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Контакт з таким email або телефоном вже існує",
        )
    except Exception as e:
        logger.error("Неочікувана помилка при оновленні контакту: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося оновити контакт. Спробуйте ще раз.",
        )


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Видалити контакт за ідентифікатором.
    """
    logger.info("Спроба видалити контакт з id: %d", contact_id)
    contact_service = ContactService(db)
    deleted_contact = await contact_service.remove_contact(contact_id, user.id)
    if not deleted_contact:
        logger.error(
            "Не вдалося видалити контакт. Контакт з id %d не знайдено", contact_id
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    logger.info("Контакт з id %d успішно видалено", contact_id)
    return None
