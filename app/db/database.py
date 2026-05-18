"""
Gestionnaire de connexion à PostgreSQL avec SQLAlchemy async
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from app.core.config import get_settings
from app.db.models import Base

logger = logging.getLogger(__name__)
settings = get_settings()


# Moteur async pour les opérations normales (optimized for high performance)
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=getattr(settings, 'DB_POOL_SIZE', 50),
    max_overflow=getattr(settings, 'DB_MAX_OVERFLOW', 100),
    pool_pre_ping=True,
    pool_recycle=getattr(settings, 'DB_POOL_RECYCLE', 3600),
    pool_timeout=getattr(settings, 'DB_POOL_TIMEOUT', 30),
    connect_args={
        "server_settings": {
            "application_name": "chatbot_l0027",
            "tcp_keepalives_idle": "600",
            "tcp_keepalives_interval": "30",
            "tcp_keepalives_count": "3",
        }
    },
)

# Session factory async
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Moteur sync pour les migrations et scripts
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=0,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Initialise la base de données (crée les tables)"""
    import asyncio
    max_retries = 10
    retry_delay = 3  # seconds
    initial_delay = 2  # Wait a bit before first attempt to ensure DNS is ready
    
    # Initial delay to ensure network/DNS is ready
    logger.info(f"⏳ Attente de {initial_delay}s avant la première tentative de connexion...")
    await asyncio.sleep(initial_delay)
    
    for attempt in range(max_retries):
        try:
            # Test DNS resolution first
            import socket
            try:
                host = settings.POSTGRES_HOST
                port = settings.POSTGRES_PORT
                logger.debug(f"Résolution DNS de '{host}':{port}...")
                ip = socket.gethostbyname(host)
                logger.debug(f"✅ DNS résolu: {host} -> {ip}")
            except Exception as dns_error:
                logger.warning(f"⚠️ Résolution DNS échouée (tentative {attempt + 1}): {dns_error}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise
            
            # Attempt database connection
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Base de données initialisée avec succès")
            return
        except Exception as e:
            error_msg = str(e)
            if attempt < max_retries - 1:
                logger.warning(f"⚠️ Tentative de connexion à PostgreSQL échouée (tentative {attempt + 1}/{max_retries}): {error_msg}")
                logger.info(f"⏳ Nouvelle tentative dans {retry_delay} secondes...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"❌ Impossible de se connecter à PostgreSQL après {max_retries} tentatives")
                logger.error(f"Dernière erreur: {error_msg}")
                logger.error(f"Host: {settings.POSTGRES_HOST}, Port: {settings.POSTGRES_PORT}, DB: {settings.POSTGRES_DB}")
                raise


async def close_db():
    """Ferme les connexions à la base de données"""
    await async_engine.dispose()
    logger.info("Connexions à la base de données fermées")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency pour obtenir une session de base de données"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager pour les opérations DB hors FastAPI"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Vérifie la connexion à la base de données"""
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Erreur de connexion à PostgreSQL: {e}")
        return False


def get_sync_db():
    """Obtenir une session synchrone (pour scripts)"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()