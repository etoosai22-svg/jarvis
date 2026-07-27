import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """로컬 편의용 스키마 생성. 운영 스키마는 Alembic이 담당한다."""
    if not settings.auto_create_tables:
        logger.info("auto_create_tables=false — 스키마는 alembic upgrade head로 관리합니다.")
        return

    # 메타데이터를 채우기 위해 모델을 import한다.
    from app.models import audit_log, conversation, memory, message, preference, task, user  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
