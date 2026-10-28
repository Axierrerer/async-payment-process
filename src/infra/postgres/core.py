from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.settings import AllSettings


def get_engine(settings: AllSettings) -> AsyncEngine:
    db_settings = settings.postgres
    return create_async_engine(
        url=db_settings.async_url,
        pool_size=db_settings.POOL_SIZE,
        max_overflow=db_settings.MAX_OVERFLOW,
        pool_pre_ping=db_settings.POOL_PRE_PING,
    )


def get_async_session_factory(
    async_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
