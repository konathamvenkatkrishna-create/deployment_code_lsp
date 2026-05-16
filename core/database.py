# core/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core.config import settings


# ============================================================
# Engine Configuration
# ============================================================
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,              # Turn True only during debugging
    pool_pre_ping=True,      # Prevent stale DB connections
    pool_size=5,             # Connection pool size
    max_overflow=10,         # Extra connections beyond pool_size
)


# ============================================================
# Session Configuration
# ============================================================
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# Base Model for All ORM Models
# ============================================================
class Base(DeclarativeBase):
    pass


# ============================================================
# Database Dependency (FastAPI)
# ============================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()