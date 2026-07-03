from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from filmcortex.config.settings import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
