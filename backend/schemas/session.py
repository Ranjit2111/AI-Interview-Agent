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

class SessionEndResponse(BaseModel):
    """Schema for the response when ending a session."""
    status: str = Field(..., description="Status message (e.g., 'Interview Ended')")
    session_id: str = Field(..., description="The ID of the session that ended")
    # Final results are now embedded
    coaching_summary: Optional[Dict[str, Any]] = Field(None, description="Final coaching summary JSON")
    skill_profile: Optional[Dict[str, Any]] = Field(None, description="Final skill assessment profile JSON")

    class Config:
        from_attributes = True
        populate_by_name = True # Allows using 'id' alias

# Removed SessionInfo and SessionMetrics as they appear unused and tied to old DB structure
# class SessionInfo(BaseModel):
#    ...
# class SessionMetrics(BaseModel):
#    ...

# Removed SessionMode enum as it was unused
# class SessionMode(str, enum.Enum):
#    ... 