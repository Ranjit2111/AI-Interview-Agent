"""
Database connection module for SQLAlchemy ORM.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure logging
logger = logging.getLogger(__name__)

# Load database URL from environment or use SQLite default
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./interview_app.db")
logger.info(f"Using database: {DATABASE_URL}")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False  # Set to True to see SQL statements
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Import models to include in metadata
# Note: These imports are here to ensure the models are registered with the Base metadata
from backend.models.interview import InterviewSession, Message, Question, Answer, SkillAssessment, Resource
from backend.models.transcript import Transcript, TranscriptTag, TranscriptEmbedding, TranscriptFragment

def init_db():
    """
    Initialize the database by creating all tables.
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

def get_db():
    """
    Get a database session.
    
    Yields:
        SQLAlchemy database session
    """
    logger.debug("Attempting to get DB session...")
    db = SessionLocal()
    logger.debug(f"DB session created: {db}")
    try:
        yield db
        logger.debug(f"DB session yielded: {db}")
    except Exception as e:
        logger.exception(f"Exception during DB session yield: {e}")
        raise
    finally:
        logger.debug(f"Closing DB session: {db}")
        db.close() 