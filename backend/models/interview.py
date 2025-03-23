"""
Interview models for the interview preparation system.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from typing import Dict, Any, List, Optional
import json

from backend.database.connection import Base


class InterviewStyle(enum.Enum):
    """
    Enumeration of available interview styles.
    """
    FORMAL = "formal"
    CASUAL = "casual"
    AGGRESSIVE = "aggressive"
    TECHNICAL = "technical"


class SessionMode(enum.Enum):
    """
    Enumeration of available session modes.
    """
    INTERVIEW = "interview"
    COACHING = "coaching"
    SKILL_ASSESSMENT = "skill_assessment"


class ProficiencyLevel(enum.Enum):
    """
    Enumeration of skill proficiency levels.
    """
    BEGINNER = "beginner"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SkillCategory(enum.Enum):
    """
    Enumeration of skill categories.
    """
    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    TOOL = "tool"
    METHODOLOGY = "methodology"


class InterviewSession(Base):
    """
    Interview session model representing a complete interview interaction.
    """
    __tablename__ = "interview_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    job_role = Column(String(255))
    job_description = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)
    style = Column(Enum(InterviewStyle), default=InterviewStyle.FORMAL)
    mode = Column(Enum(SessionMode), default=SessionMode.INTERVIEW)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="interview_sessions")
    questions = relationship("Question", back_populates="interview_session", cascade="all, delete-orphan")
    skill_assessments = relationship("SkillAssessment", back_populates="interview_session", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    transcripts = relationship("Transcript", back_populates="interview_session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<InterviewSession(id={self.id}, job_role='{self.job_role}', mode='{self.mode.value}')>"


class Question(Base):
    """
    Question model representing a single interview question.
    """
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    text = Column(Text, nullable=False)
    difficulty = Column(Integer, default=1)  # 1-5 scale
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview_session = relationship("InterviewSession", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Question(id={self.id}, text='{self.text[:30]}...')>"


class Answer(Base):
    """
    Answer model representing a user's response to an interview question.
    """
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    text = Column(Text, nullable=False)
    audio_path = Column(String, nullable=True)
    feedback = Column(Text, nullable=True)
    star_rating = Column(JSON, nullable=True)  # JSON with S, T, A, R ratings
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    question = relationship("Question", back_populates="answers")
    
    def __repr__(self):
        return f"<Answer(id={self.id}, text='{self.text[:30]}...')>"


class SkillAssessment(Base):
    """
    Skill assessment model representing the evaluation of a user's skills.
    """
    __tablename__ = "skill_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_session_id = Column(String(255), ForeignKey("interview_sessions.session_id"))
    skill_name = Column(String(255))
    category = Column(String(50))
    proficiency_level = Column(Enum(ProficiencyLevel), nullable=False)
    confidence = Column(Float, default=0.0)  # Confidence score of the assessment (0.0 - 1.0)
    feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interview_session = relationship("InterviewSession", back_populates="skill_assessments")
    resources = relationship("Resource", back_populates="skill_assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SkillAssessment(id={self.id}, skill_name='{self.skill_name}', proficiency_level='{self.proficiency_level.value}')>"


class Resource(Base):
    """
    Resource model representing learning resources recommended to improve skills.
    """
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    skill_assessment_id = Column(Integer, ForeignKey("skill_assessments.id"))
    title = Column(String(255))
    url = Column(String(255))
    description = Column(Text)
    resource_type = Column(String(50))
    relevance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    skill_assessment = relationship("SkillAssessment", back_populates="resources")
    
    def __repr__(self):
        return f"<Resource(id={self.id}, title='{self.title}', resource_type='{self.resource_type}')>"


class Message(Base):
    """Model for interview messages."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("interview_sessions.session_id"))
    role = Column(String(50))  # user or assistant
    agent = Column(String(50), nullable=True)  # for assistant messages
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("InterviewSession", back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "agent": self.agent,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class ResourceTracking(Base):
    """Model for tracking resource usage."""
    __tablename__ = "resource_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True)
    resource_id = Column(String(255), index=True)  # Could be database ID or URL
    action = Column(String(50))  # click, bookmark, etc.
    skill_name = Column(String(255), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "resource_id": self.resource_id,
            "action": self.action,
            "skill_name": self.skill_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata
        }


class ResourceFeedback(Base):
    """Model for resource feedback."""
    __tablename__ = "resource_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True)
    resource_id = Column(String(255), index=True)  # Could be database ID or URL
    feedback = Column(String(50))  # helpful, not_helpful
    skill_name = Column(String(255), index=True)
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "resource_id": self.resource_id,
            "feedback": self.feedback,
            "skill_name": self.skill_name,
            "comments": self.comments,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        } 