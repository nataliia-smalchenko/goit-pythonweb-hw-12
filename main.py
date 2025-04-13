import logging
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager


from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.database.db import get_db, sessionmanager
from src.api import contacts, auth, users  # імпортуємо наші маршрути для контактів


logger = logging.getLogger("uvicorn.error")

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
]

scheduler = AsyncIOScheduler()


async def cleanup_expired_tokens():
    async with sessionmanager.session() as db:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=7)
        stmt = text(
            "DELETE FROM refresh_tokens WHERE expired_at < :now OR revoked_at IS NOT NULL AND revoked_at < :cutoff"
        )
        await db.execute(stmt, {"now": now, "cutoff": cutoff})
        await db.commit()
        print(f"Expired tokens cleaned up [{now.strftime('%Y-%m-%d %H:%M:%S')}]")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(cleanup_expired_tokens, "interval", hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Contacts API",
    description="REST API для управління контактами",
    version="1.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error: %s", exc.errors())
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {
                "detail": exc.errors(),
                "message": "Помилка валідації. Перевірте передані дані.",
            }
        ),
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Підключаємо маршрути контакту з префіксом /api
app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/", response_model=dict)
async def read_root(request: Request):
    """
    Кореневий ендпоінт, що повертає повідомлення про версію додатку.
    """
    return {"message": "Contacts Application v1.0"}


@app.get("/api/healthchecker", response_model=dict)
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    Ендпоінт для перевірки працездатності бази даних.
    Виконується простий запит до БД для перевірки з'єднання.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
        return {"message": "Welcome to Contacts API!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )
