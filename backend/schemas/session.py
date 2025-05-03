"""
Pydantic schemas for interview sessions and agent interactions.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import enum

# Import enums from models to ensure consistency
from backend.models.interview import InterviewStyle

# --- Input Schemas ---

class InterviewConfig(BaseModel):
    """Schema for configuring a new interview session."""
    job_role: str = Field(..., description="Target job role for the interview")
    job_description: Optional[str] = Field(None, description="Detailed job description")
    resume_content: Optional[str] = Field(None, description="Content of the user's resume")
    company_name: Optional[str] = Field(None, description="Company name")
    interview_style: Optional[str] = Field(InterviewStyle.FORMAL.value, description="Style of interview (FORMAL, CASUAL, AGGRESSIVE, TECHNICAL)")
    question_count: Optional[int] = Field(5, description="Target number of questions")
    difficulty_level: Optional[str] = Field("medium", description="Difficulty level")
    user_id: Optional[str] = Field(None, description="User identifier associated with the session")

    class Config:
        from_attributes = True


class UserMessage(BaseModel):
    """Schema for user messages sent during an interview."""
    message: str = Field(..., description="The user's message text")
    user_id: Optional[str] = Field(None, description="User identifier (optional, might be inferred from session)")

    class Config:
        from_attributes = True

class CoachingRequestData(BaseModel):
    """Schema for data sent in a coaching request."""
    request_type: str = Field(..., description="Type of coaching requested (e.g., 'tips', 'practice_question', 'template')")
    details: Optional[Dict[str, Any]] = Field(None, description="Specific details for the request (e.g., focus area for tips, question type)")

    class Config:
        from_attributes = True


# --- Output Schemas ---

class SessionStartResponse(BaseModel):
    """Schema for the response when starting a session."""
    session_id: str = Field(..., description="The unique ID for the new session")
    message: str = Field("Session created successfully.", description="Status message")
    # Optionally include initial metadata if useful for the client
    # initial_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AgentResponse(BaseModel):
    """Schema for messages sent FROM the agent system TO the user."""
    role: str = Field(..., description="Role of the sender (usually 'assistant' or 'system')")
    agent: Optional[str] = Field(None, description="Specific agent sending the message (e.g., 'interviewer', 'coach')")
    content: str = Field(..., description="The message content")
    response_type: Optional[str] = Field(None, description="Type of response (e.g., 'question', 'feedback', 'closing', 'error')")
    timestamp: str = Field(..., description="ISO format timestamp of the message")
    processing_time: Optional[float] = Field(None, description="Time taken by the agent to generate the response (in seconds)")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Additional metadata associated with the message")
    is_error: Optional[bool] = Field(False, description="Indicates if this message represents an error")

    class Config:
        from_attributes = True

class SessionEndResponse(BaseModel):
    """Schema for the response when ending a session."""
    status: str = Field(..., description="Status message (e.g., 'Interview Ended')")
    session_id: str = Field(..., description="The ID of the session that ended")
    # Final results are now embedded
    coaching_summary: Optional[Dict[str, Any]] = Field(None, description="Final coaching summary JSON")
    skill_profile: Optional[Dict[str, Any]] = Field(None, description="Final skill assessment profile JSON")

    class Config:
        from_attributes = True

class SessionInfo(BaseModel):
    """Schema for retrieving basic information about a session."""
    session_id: str = Field(..., alias='id') # Use alias if DB model uses 'id'
    user_id: Optional[str] = None
    job_role: str
    job_description: Optional[str] = None
    # resume_content: Optional[str] = None # Exclude potentially large fields from basic info?
    style: InterviewStyle # Use the enum directly
    mode: SessionMode # Use the enum directly
    difficulty: Optional[str] = None
    target_question_count: Optional[int] = None
    company_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    # Include fields derived from results if needed, e.g., overall score?
    # overall_score: Optional[float] = None

    class Config:
        from_attributes = True
        populate_by_name = True # Allows using 'id' alias


class SessionMetrics(BaseModel):
    """Schema for session performance metrics."""
    session_id: str
    total_messages: int
    user_message_count: int
    assistant_message_count: int
    average_user_message_length: float
    average_assistant_message_length: float
    average_response_time_seconds: Optional[float] = None
    average_processing_time_seconds: Optional[float] = None
    conversation_duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True
        populate_by_name = True

# Need SessionMode enum if used in SessionInfo
class SessionMode(str, enum.Enum):
    INTERVIEW = "interview"
    COACHING = "coaching"
    SKILL_ASSESSMENT = "skill_assessment"

# Need InterviewStyle enum if used in SessionInfo (re-declare or ensure import works)
# class InterviewStyle(str, enum.Enum):
#     FORMAL = "formal"
#     CASUAL = "casual"
#     AGGRESSIVE = "aggressive"
#     TECHNICAL = "technical" 