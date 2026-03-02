"""Database connection and session management.

This module provides SQLAlchemy engine and session factory for database operations.
Supports both SQLite and PostgreSQL databases.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.config import get_database_url, settings


# Create engine based on database type
def create_db_engine():
    """
    Create SQLAlchemy engine based on configuration.

    Returns:
        SQLAlchemy Engine instance
    """
    database_url = get_database_url()

    # Special handling for SQLite
    if database_url.startswith("sqlite"):
        # For SQLite, use StaticPool for better thread safety
        # and check_same_thread=False for cross-thread access
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        # For PostgreSQL and other databases
        engine = create_engine(database_url)

    return engine


# Create engine instance
engine = create_db_engine()

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create declarative base for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.

    Yields:
        Database session

    Usage:
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.

    Creates all tables defined by models.
    """
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
