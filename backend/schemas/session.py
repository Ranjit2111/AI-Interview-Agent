"""
Pydantic schemas for interview sessions and agent interactions.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import enum

from backend.models.interview import InterviewStyle

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

class CoachAnswerFeedback(BaseModel):
    """Schema for structured feedback on a single answer from CoachAgent."""
    conciseness: str = Field(..., description="Feedback on the conciseness of the answer.")
    completeness: str = Field(..., description="Feedback on the completeness of the answer.")
    technical_accuracy_depth: str = Field(..., description="Feedback on technical accuracy and depth.")
    contextual_alignment: str = Field(..., description="Feedback on alignment with resume and job description.")
    fixes_improvements: str = Field(..., description="Actionable advice for improving the answer.")
    star_support: str = Field(..., description="Feedback on the use of STAR method, if applicable.")
    error: Optional[str] = Field(None, description="Error message if feedback generation failed for this answer.")

    class Config:
        from_attributes = True

class InterviewerResponse(BaseModel):
    """Schema for the interviewer's part of the response."""
    content: str = Field(..., description="The question or statement from the interviewer.")
    response_type: str = Field(..., description="Type of response (e.g., 'question', 'closing_statement').")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata, e.g., question number, justification.")

    class Config:
        from_attributes = True

class AgentMessageResponse(BaseModel):
    """
    Schema for the combined response after a user message is processed.
    Includes the interviewer's next response and the coach's feedback on the user's last answer.
    """
    session_id: str = Field(..., description="The ID of the current session.")
    interviewer_response: InterviewerResponse = Field(..., description="The interviewer's response (e.g., next question).")
    coach_feedback: Optional[CoachAnswerFeedback] = Field(None, description="Feedback from the CoachAgent on the user's last answer.")
    # event_type: Optional[str] = Field(None, description="Indicator of the current phase or event, e.g., 'interview_turn', 'feedback_provided'.") # Optional, can be added if useful for frontend
    
    class Config:
        from_attributes = True

class SessionStartResponse(BaseModel):
    """Schema for the response when starting a session."""
    session_id: str = Field(..., description="The unique ID for the new session")
    message: str = Field("Session created successfully.", description="Status message")

    class Config:
        from_attributes = True

class FinalCoachingSummary(BaseModel):
    """Schema for the detailed final coaching summary from CoachAgent."""
    patterns_tendencies: str = Field(..., description="Observed patterns and tendencies in candidate's responses.")
    strengths: str = Field(..., description="Key strengths demonstrated by the candidate.")
    weaknesses: str = Field(..., description="Key weaknesses or areas for development.")
    improvement_focus_areas: str = Field(..., description="Suggested areas to focus on for improvement.")
    resource_search_topics: List[str] = Field(default_factory=list, description="Specific topics for resource searches.")
    recommended_resources: Optional[List[Dict[str, Any]]] = Field(None, description="Curated resources based on search topics (populated by orchestrator).")
    error: Optional[str] = Field(None, description="Error message if final summary generation failed.")
    
    class Config:
        from_attributes = True

class SessionEndResponse(BaseModel):
    """Schema for the response when ending a session."""
    status: str = Field(..., description="Status message (e.g., 'Interview Ended')")
    session_id: str = Field(..., description="The ID of the session that ended")
    coaching_summary: Optional[FinalCoachingSummary] = Field(None, description="Final coaching summary object.")

    class Config:
        from_attributes = True
        populate_by_name = True