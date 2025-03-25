"""
Transcript models for the interview preparation system.
Provides data structures for storing, tagging, and retrieving interview transcripts.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Table, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from typing import Dict, Any, List, Optional

from backend.database.connection import Base


class TranscriptFormat(enum.Enum):
    """
    Enumeration of available transcript export/import formats.
    """
    JSON = "json"
    CSV = "csv"
    TEXT = "text"
    MARKDOWN = "markdown"


class TranscriptTag(Base):
    """
    Model for transcript tags to categorize transcripts.
    """
    __tablename__ = "transcript_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    description = Column(String(255), nullable=True)
    color = Column(String(7), default="#3a3a3a")  # Hex color code
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transcripts = relationship(
        "Transcript",
        secondary="transcript_tag_association",
        back_populates="tags"
    )
    
    def __repr__(self):
        return f"<TranscriptTag(id={self.id}, name='{self.name}')>"


# Association table for many-to-many relationship between transcripts and tags
transcript_tag_association = Table(
    "transcript_tag_association",
    Base.metadata,
    Column("transcript_id", Integer, ForeignKey("transcripts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("transcript_tags.id"), primary_key=True)
)


class Transcript(Base):
    """
    Transcript model for storing complete interview transcripts.
    """
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    interview_session_id = Column(String(255), ForeignKey("interview_sessions.session_id"), nullable=True)
    user_id = Column(String(255), nullable=True, index=True)
    content = Column(JSON, nullable=False)  # JSON array of conversation messages
    summary = Column(Text, nullable=True)
    transcript_metadata = Column(JSON, nullable=True)  # Additional metadata (renamed from metadata)
    is_imported = Column(Boolean, default=False)  # Whether this was imported or generated
    is_public = Column(Boolean, default=False)  # Whether this transcript is publicly accessible
    vector_id = Column(String(255), nullable=True)  # ID in the vector store
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interview_session = relationship("InterviewSession", back_populates="transcripts")
    tags = relationship(
        "TranscriptTag",
        secondary="transcript_tag_association",
        back_populates="transcripts"
    )
    embeddings = relationship("TranscriptEmbedding", back_populates="transcript", cascade="all, delete-orphan")
    fragments = relationship("TranscriptFragment", back_populates="transcript", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Transcript(id={self.id}, title='{self.title}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "interview_session_id": self.interview_session_id,
            "user_id": self.user_id,
            "summary": self.summary,
            "transcript_metadata": self.transcript_metadata,
            "is_imported": self.is_imported,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": [tag.name for tag in self.tags] if self.tags else []
        }


class TranscriptEmbedding(Base):
    """
    Model for storing embeddings of transcript content for semantic search.
    """
    __tablename__ = "transcript_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"))
    model_name = Column(String(255))  # Name of the embedding model used
    embedding_file = Column(String(255))  # Path to stored embedding file
    dimensions = Column(Integer, nullable=True)  # Embedding dimensions
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transcript = relationship("Transcript", back_populates="embeddings")
    
    def __repr__(self):
        return f"<TranscriptEmbedding(id={self.id}, model_name='{self.model_name}')>"


class TranscriptFragment(Base):
    """
    Model for storing fragments of transcripts for more granular retrieval.
    """
    __tablename__ = "transcript_fragments"
    
    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"))
    content = Column(Text, nullable=False)
    start_index = Column(Integer, nullable=True)  # Start index in the original transcript
    end_index = Column(Integer, nullable=True)  # End index in the original transcript
    embedding_vector = Column(String(255), nullable=True)  # Reference to vector in FAISS
    relevance_score = Column(Float, default=0.0)  # Relevance score (0.0 - 1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transcript = relationship("Transcript", back_populates="fragments")
    
    def __repr__(self):
        return f"<TranscriptFragment(id={self.id}, relevance_score={self.relevance_score})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "transcript_id": self.transcript_id,
            "content": self.content,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 