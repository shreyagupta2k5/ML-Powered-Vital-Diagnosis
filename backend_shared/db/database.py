# backend_shared/db/database.py
"""Database engine, session management, and initialization."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from .models import Base

# SQLite for dev, PostgreSQL for prod (via DATABASE_URL env var)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend_shared/backend.db")

# SQLite requires check_same_thread=False for FastAPI compatibility
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db_session() -> Session:
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()