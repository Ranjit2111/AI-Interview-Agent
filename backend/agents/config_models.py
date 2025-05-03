"""
Configuration models for interview sessions, decoupled from database models.
"""

import enum
from typing import Optional
from pydantic import BaseModel

class InterviewStyle(enum.Enum):
    """
    Enumeration of available interview styles.
    """
    FORMAL = "formal"
    CASUAL = "casual"
    AGGRESSIVE = "aggressive"
    TECHNICAL = "technical"

class SessionConfig(BaseModel):
    """
    Configuration for a single interview session.
    Used by agents to understand the context and parameters of the interview.
    """
    job_role: str = "General Role"
    job_description: Optional[str] = None
    resume_content: Optional[str] = None
    style: InterviewStyle = InterviewStyle.FORMAL
    difficulty: str = "medium"
    target_question_count: int = 5
    company_name: Optional[str] = None

    # Add pydantic config if needed, e.g., for ORM mode compatibility if used elsewhere
    # class Config:
    #     orm_mode = True # Pydantic v1
    #     from_attributes = True # Pydantic v2 