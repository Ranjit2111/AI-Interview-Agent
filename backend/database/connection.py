"""
Database connection module.
Provides SQLAlchemy engine and session management.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

# Get the database URL from environment or use a default SQLite database
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "sqlite:///./interview_agent.db"
)

# Create logger
logger = logging.getLogger(__name__)

# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Set to True to see SQL queries
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()

# Create a context manager for database sessions
@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    
    Yields:
        Session: A SQLAlchemy session.
        
    Example:
        ```python
        with get_db() as db:
            result = db.query(Model).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to initialize the database
def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    logger.info("Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise 