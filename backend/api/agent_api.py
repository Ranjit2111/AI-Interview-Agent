"""
API interface for the interview agent system.
Provides endpoints for interacting with the interview agents.
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.interview import InterviewStyle, InterviewSession
from backend.models.user import User
from backend.agents import SessionManager


class UserMessage(BaseModel):
    """Model for user messages sent to the agent system."""
    message: str = Field(..., description="The user's message text")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: str = Field(..., description="Session identifier")

    class Config:
        from_attributes = True


class InterviewConfig(BaseModel):
    """Model for configuring a new interview session."""
    job_role: str = Field(..., description="Target job role for the interview")
    job_description: Optional[str] = Field(None, description="Detailed job description")
    resume_content: Optional[str] = Field(None, description="Content of the user's resume")
    company_name: Optional[str] = Field(None, description="Company name")
    interview_style: Optional[str] = Field(InterviewStyle.FORMAL.value, description="Style of interview (FORMAL, CASUAL, AGGRESSIVE, TECHNICAL)")
    question_count: Optional[int] = Field(5, description="Target number of questions")
    difficulty_level: Optional[str] = Field("medium", description="Difficulty level")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    class Config:
        from_attributes = True


class SessionStartResponse(BaseModel):
    session_id: str = Field(..., description="The unique ID for the new session")
    initial_message: Optional[Dict[str, Any]] = Field(None, description="The initial message from the interviewer")
    
    class Config:
        from_attributes = True


class SessionEndResponse(BaseModel):
    status: str
    session_id: str
    coaching_summary: Optional[Dict[str, Any]]
    skill_profile: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str
    job_role: str
    interview_style: str
    created_at: str
    
    class Config:
        from_attributes = True


class SessionMetrics(BaseModel):
    """Model for session metrics."""
    session_id: str
    total_messages: int
    user_messages: int
    assistant_messages: int
    system_messages: int
    total_response_time_seconds: float
    average_response_time_seconds: float
    total_api_calls: int
    total_tokens_used: int
    
    class Config:
        from_attributes = True


class AgentResponse(BaseModel):
    """Model for agent responses."""
    role: str
    agent: Optional[str] = None
    content: str
    response_type: Optional[str] = None
    timestamp: str
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    is_error: Optional[bool] = False
    
    class Config:
        from_attributes = True


class SkillResource(BaseModel):
    """Model for skill improvement resources."""
    title: str
    url: str
    description: Optional[str]
    type: Optional[str]
    relevance_score: Optional[float]
    
    class Config:
        from_attributes = True


class SkillProfile(BaseModel):
    """Model for a user's complete skill profile."""
    job_role: str
    assessed_skills: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True


async def get_session_config(session_id: str, db: Session = Depends(get_db)) -> InterviewSession:
    """Placeholder: Retrieves InterviewSession config from DB."""
    session_data = db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
    if not session_data:
        raise HTTPException(status_code=404, detail=f"Session config {session_id} not found")
    return session_data


async def get_session_manager_instance(
    session_id: str = Query(...),
    db: Session = Depends(get_db)
) -> SessionManager:
    """
    FastAPI dependency to get a SessionManager instance for a given session ID.
    Retrieves config from DB and instantiates the manager.
    """
    try:
        session_config = await get_session_config(session_id, db)
        user_id = session_config.user_id 
        manager = SessionManager(
            session_id=session_id,
            user_id=user_id, 
            session_config=session_config
        )
        return manager
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.exception(f"Failed to get/create SessionManager for {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Could not load session manager.")


def create_agent_api(app: FastAPI):
    """
    Create API endpoints for the agent system.
    """
    logger = logging.getLogger(__name__)
    
    @app.post("/api/interview/start", response_model=SessionStartResponse)
    async def start_interview(config: InterviewConfig, db: Session = Depends(get_db)):
        """
        Start a new interview session.
        Creates InterviewSession, persists it, initializes SessionManager, gets first message.
        """
        logger.info(f"Entered start_interview endpoint for role: {config.job_role}") 
        session_id = str(uuid.uuid4())
        logger.info(f"Attempting to start interview session {session_id}...")
        try:
            logger.info("Mapping config to InterviewSession model...")
            session_data = InterviewSession(
                session_id=session_id,
                user_id=config.user_id,
                job_role=config.job_role,
                job_description=config.job_description,
                resume_text=config.resume_content, 
                style=InterviewStyle(config.interview_style or InterviewStyle.FORMAL.value), 
                created_at=datetime.utcnow(), 
            )
            logger.info("InterviewSession object created in memory.")
            
            db.add(session_data)
            logger.info("Added session_data to DB session.")
            db.commit()
            logger.info("DB commit successful.")
            db.refresh(session_data)
            logger.info(f"Interview session {session_id} persisted and refreshed.")

            logger.info("Initializing SessionManager...")
            manager = SessionManager(
                session_id=session_id,
                user_id=config.user_id,
                session_config=session_data
            )
            logger.info("SessionManager initialized.")
            
            logger.info("Processing initial message...")
            initial_response = manager.process_message("")
            logger.info("Initial message processed.")
            
            return SessionStartResponse(
                session_id=session_id,
                initial_message=initial_response
            )
            
        except ValueError as ve:
            logger.exception(f"Value error during session start (likely invalid style '{config.interview_style}'): {ve}")
            raise HTTPException(status_code=400, detail=f"Invalid configuration value: {ve}")
        except Exception as e:
            logger.exception(f"Unhandled error starting interview session {session_id}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to start interview session.")
    
    @app.post("/api/interview/send", response_model=AgentResponse)
    async def send_message(
        message: UserMessage,
        manager: SessionManager = Depends(lambda message_body: get_session_manager_instance(session_id=message_body.session_id), use_cache=False)
    ):
        """
        Send a message to an ongoing interview session.
        """
        logger.info(f"Received message for session {message.session_id}")
        agent_response = manager.process_message(message.message, message.user_id)
        return AgentResponse(**agent_response)
    
    @app.post("/api/interview/end", response_model=SessionEndResponse)
    async def end_interview(
        session_id: str = Query(...),
        manager: SessionManager = Depends(get_session_manager_instance)
    ):
        """
        End an interview session and get final summaries.
        """
        logger.info(f"Ending interview session {session_id}")
        final_results = manager.end_interview()
        return SessionEndResponse(**final_results)
    
    @app.get("/api/interview/history", response_model=List[AgentResponse])
    async def get_conversation_history(
        session_id: str = Query(...),
        manager: SessionManager = Depends(get_session_manager_instance)
    ):
        """
        Get the conversation history for a session.
        """
        logger.info(f"Fetching history for session {manager.session_id}")
        return [AgentResponse(**msg) for msg in manager.get_conversation_history()]

    @app.get("/api/interview/stats", response_model=SessionMetrics)
    async def get_session_stats(
        session_id: str = Query(...),
        manager: SessionManager = Depends(get_session_manager_instance)
    ):
        """
        Get performance statistics for a session.
        """
        logger.info(f"Fetching stats for session {manager.session_id}")
        return SessionMetrics(**manager.get_session_stats())

    @app.get("/api/interview/skill-profile", response_model=SkillProfile)
    async def get_skill_profile_endpoint(
        session_id: str = Query(...),
        manager: SessionManager = Depends(get_session_manager_instance)
    ):
        """
        Get the generated skill profile for a session (usually after ending).
        """
        logger.info(f"Fetching skill profile for session {manager.session_id}")
        skill_agent = manager._get_agent('skill_assessor')
        if skill_agent and hasattr(skill_agent, 'generate_skill_profile'):
            profile = skill_agent.generate_skill_profile()
            if isinstance(profile, dict) and "error" in profile:
                raise HTTPException(status_code=500, detail=profile["error"])
            try:
                return SkillProfile(**profile)
            except Exception as validation_error:
                logger.error(f"Skill profile validation failed for session {manager.session_id}: {validation_error}")
                raise HTTPException(status_code=500, detail="Failed to validate skill profile structure.")
        else:
            logger.error(f"Skill assessor not available for session {manager.session_id}")
            raise HTTPException(status_code=500, detail="Skill assessment not available.")

    @app.get("/api/interview/skill-resources", response_model=List[SkillResource])
    async def get_skill_resources_endpoint(
        skill_name: str = Query(...),
        session_id: str = Query(...),
        manager: SessionManager = Depends(get_session_manager_instance)
    ):
        """
        Get suggested resources for improving a specific skill.
        """
        logger.info(f"Fetching resources for skill '{skill_name}' in session {manager.session_id}")
        skill_agent = manager._get_agent('skill_assessor')
        if skill_agent and hasattr(skill_agent, 'get_suggested_resources'):
            resources = skill_agent.get_suggested_resources(skill_name)
            try:
                return [SkillResource(**res) for res in resources]
            except Exception as validation_error:
                logger.error(f"Skill resource validation failed for session {manager.session_id}: {validation_error}")
                raise HTTPException(status_code=500, detail="Failed to validate skill resource structure.")
        else:
            logger.error(f"Skill assessor not available for session {manager.session_id}")
            raise HTTPException(status_code=500, detail="Skill assessment not available.")

    logger.info("Agent API endpoints created.")

    return app 