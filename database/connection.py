"""
Database Connection and Session Management for BankFreeze AI
Provides SQLite connection, SessionLocal factory, and DB initializers.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from config.settings import settings
from database.models import Base

# Create SQLite engine
# connect_args={"check_same_thread": False} is required for SQLite when used with Streamlit multi-threading
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def reset_db():
    """Drop and recreate all database tables (used for testing and demo resets)."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
