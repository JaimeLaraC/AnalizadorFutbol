"""
Configuración de la base de datos PostgreSQL.

Proporciona la conexión, sesión y base declarativa para SQLAlchemy.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ..utils.config import settings


# Crear engine de SQLAlchemy
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL en modo debug
    pool_pre_ping=True,  # Verificar conexión antes de usar
    pool_size=5,
    max_overflow=10
)

# Sesión local
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base para modelos declarativos
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Generador de sesión de base de datos.
    
    Uso con FastAPI:
        @app.get("/")
        def read(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager para sesión de base de datos.
    
    Uso:
        with get_db_session() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Inicializa la base de datos creando todas las tablas.
    
    Solo usar en desarrollo o para setup inicial.
    En producción usar Alembic para migraciones.
    """
    Base.metadata.create_all(bind=engine)
