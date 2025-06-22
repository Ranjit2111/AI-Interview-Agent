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
    target_question_count: Optional[int] = 15  # Fallback for question-based interviews
    company_name: Optional[str] = None
    interview_duration_minutes: Optional[int] = 10  # Default to 10-minute interviews
    use_time_based_interview: bool = True  # Enable time-based interviews by default
