"""
Interview models for the interview preparation system.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

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
    user_id = Column(Integer, ForeignKey("users.id"))
    job_role = Column(String, nullable=False)
    job_description = Column(Text, nullable=True)
    resume_text = Column(Text, nullable=True)
    style = Column(Enum(InterviewStyle), default=InterviewStyle.FORMAL)
    mode = Column(Enum(SessionMode), default=SessionMode.INTERVIEW)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="interview_sessions")
    questions = relationship("Question", back_populates="interview_session", cascade="all, delete-orphan")
    skill_assessments = relationship("SkillAssessment", back_populates="interview_session", cascade="all, delete-orphan")
    
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
    interview_session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    skill_name = Column(String, nullable=False)
    category = Column(Enum(SkillCategory), nullable=False)
    proficiency_level = Column(Enum(ProficiencyLevel), nullable=False)
    confidence = Column(Float, default=0.0)  # Confidence score of the assessment (0.0 - 1.0)
    feedback = Column(Text, nullable=True)
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
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(String, nullable=False)  # Article, Course, Video, etc.
    relevance_score = Column(Float, default=0.0)  # Relevance score (0.0 - 1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    skill_assessment = relationship("SkillAssessment", back_populates="resources")
    
    def __repr__(self):
        return f"<Resource(id={self.id}, title='{self.title}', resource_type='{self.resource_type}')>" 