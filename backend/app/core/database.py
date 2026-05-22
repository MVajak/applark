from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine: AsyncEngine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
