"""
Database Session Configuration
SQLAlchemy 2.0 async setup
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from app.core.config import settings


# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,  # Log SQL en desarrollo
    future=True,
    pool_pre_ping=True,  # Verificar conexiones antes de usar
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # No expire objects después de commit
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener database session
    
    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    
    Yields:
        AsyncSession
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Inicializar database (crear tablas si no existen)
    NOTA: En producción usar Alembic migrations
    """
    from app.db.base import Base
    
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)  # Solo para dev/test
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Cerrar conexiones de database al shutdown
    """
    await engine.dispose()
