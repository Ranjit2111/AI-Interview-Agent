"""
API interface for the interview agent system.
Provides endpoints for interacting with the interview agents.
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.interview import InterviewStyle, InterviewSession
from backend.models.user import User
from backend.agents import AgentOrchestrator, OrchestratorMode


# Global orchestrator instances cache
# Maps session_id to orchestrator instance
orchestrators = {}


class UserMessage(BaseModel):
    """Model for user messages sent to the agent system."""
    message: str = Field(..., description="The user's message text")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")


class AgentResponse(BaseModel):
    """Model for agent responses."""
    message: str = Field(..., description="The agent's response text")
    session_id: str = Field(..., description="Session identifier")
    agent_id: str = Field(..., description="Identifier of the agent that generated the response")
    timestamp: str = Field(..., description="ISO timestamp of when the response was generated")


class InterviewConfig(BaseModel):
    """Model for interview configuration."""
    job_role: str = Field(..., description="Target job role for the interview")
    job_description: Optional[str] = Field("", description="Description of the job")
    interview_style: str = Field("formal", description="Style of the interview (formal, casual, aggressive, technical)")
    user_id: Optional[str] = Field(None, description="User identifier")
    mode: str = Field(OrchestratorMode.INTERVIEW_WITH_COACHING, description="Operation mode for the orchestrator")


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str = Field(..., description="Session identifier")
    job_role: str = Field(..., description="Target job role for the interview")
    interview_style: str = Field(..., description="Style of the interview")
    mode: str = Field(..., description="Current orchestrator mode")
    created_at: str = Field(..., description="ISO timestamp of when the session was created")
    active_agent: str = Field(..., description="Currently active agent")


def get_orchestrator(session_id: str) -> AgentOrchestrator:
    """
    Get the orchestrator for a session.
    
    Args:
        session_id: The session identifier
        
    Returns:
        The orchestrator for the session
        
    Raises:
        HTTPException: If the session is not found
    """
    if session_id not in orchestrators:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return orchestrators[session_id]


def create_agent_api(app: FastAPI):
    """
    Create API endpoints for the agent system.
    
    Args:
        app: The FastAPI application
    """
    
    @app.post("/api/interview/start", response_model=SessionInfo)
    def start_interview(config: InterviewConfig, db: Session = Depends(get_db)):
        """
        Start a new interview session.
        
        Args:
            config: Interview configuration
            db: Database session
            
        Returns:
            Information about the created session
        """
        # Create a new session ID
        session_id = str(uuid.uuid4())
        
        # Map string style to enum
        try:
            style = InterviewStyle(config.interview_style.upper())
        except ValueError:
            # Default to formal if invalid style
            style = InterviewStyle.FORMAL
        
        # Create a new orchestrator
        orchestrator = AgentOrchestrator(
            mode=config.mode,
            job_role=config.job_role,
            job_description=config.job_description,
            interview_style=style
        )
        
        # Store in cache
        orchestrators[session_id] = orchestrator
        
        # Store session in database if user_id provided
        if config.user_id:
            # Check if user exists
            user = db.query(User).filter(User.id == config.user_id).first()
            
            if not user:
                raise HTTPException(status_code=404, detail=f"User {config.user_id} not found")
            
            # Create interview session
            interview_session = InterviewSession(
                id=session_id,
                user_id=config.user_id,
                job_role=config.job_role,
                job_description=config.job_description,
                style=style,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(interview_session)
            db.commit()
        
        # Initiate the interview
        welcome_message = orchestrator.process_input("/start")
        
        # Return session info
        return {
            "session_id": session_id,
            "job_role": config.job_role,
            "interview_style": style.value,
            "mode": orchestrator.mode,
            "created_at": datetime.utcnow().isoformat(),
            "active_agent": orchestrator.active_agent_id,
            "welcome_message": welcome_message
        }
    
    @app.post("/api/interview/message", response_model=AgentResponse)
    def send_message(message: UserMessage, orchestrator: AgentOrchestrator = Depends(get_orchestrator)):
        """
        Send a message to the interview agents.
        
        Args:
            message: The user's message
            orchestrator: The orchestrator for the session
            
        Returns:
            The agent's response
        """
        # Process the message
        response = orchestrator.process_input(message.message, message.user_id)
        
        # Return the response
        return {
            "message": response,
            "session_id": orchestrator.session_id,
            "agent_id": orchestrator.active_agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.post("/api/interview/end")
    def end_interview(
        session_id: str = Query(..., description="Session identifier"),
        db: Session = Depends(get_db)
    ):
        """
        End an interview session.
        
        Args:
            session_id: The session identifier
            db: Database session
            
        Returns:
            Success message
        """
        orchestrator = get_orchestrator(session_id)
        
        # End the interview
        end_message = orchestrator.process_input("/end")
        
        # Update the session in the database
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        
        if session:
            session.updated_at = datetime.utcnow()
            db.commit()
        
        # Remove from cache
        del orchestrators[session_id]
        
        return {"message": "Interview session ended", "end_message": end_message}
    
    @app.get("/api/interview/sessions", response_model=List[SessionInfo])
    def list_sessions(user_id: Optional[str] = None, db: Session = Depends(get_db)):
        """
        List active interview sessions.
        
        Args:
            user_id: Filter by user ID
            db: Database session
            
        Returns:
            List of active sessions
        """
        # Get active sessions from cache
        active_sessions = []
        
        for session_id, orchestrator in orchestrators.items():
            # Filter by user_id if provided
            if user_id and orchestrator.user_id != user_id:
                continue
            
            active_sessions.append({
                "session_id": session_id,
                "job_role": orchestrator.job_role,
                "interview_style": orchestrator.interview_style.value,
                "mode": orchestrator.mode,
                "created_at": "unknown",  # We don't track creation time in orchestrator
                "active_agent": orchestrator.active_agent_id
            })
        
        return active_sessions
    
    @app.get("/api/interview/info", response_model=SessionInfo)
    def get_session_info(session_id: str = Query(...), orchestrator: AgentOrchestrator = Depends(get_orchestrator)):
        """
        Get information about an interview session.
        
        Args:
            session_id: The session identifier
            orchestrator: The orchestrator for the session
            
        Returns:
            Session information
        """
        return {
            "session_id": session_id,
            "job_role": orchestrator.job_role,
            "interview_style": orchestrator.interview_style.value,
            "mode": orchestrator.mode,
            "created_at": "unknown",  # We don't track creation time in orchestrator
            "active_agent": orchestrator.active_agent_id
        }
    
    @app.post("/api/interview/switch-agent")
    def switch_agent(
        session_id: str = Query(..., description="Session identifier"),
        agent_id: str = Query(..., description="Agent identifier"),
        orchestrator: AgentOrchestrator = Depends(get_orchestrator)
    ):
        """
        Switch the active agent for a session.
        
        Args:
            session_id: The session identifier
            agent_id: The agent to switch to
            orchestrator: The orchestrator for the session
            
        Returns:
            Success message
        """
        # Switch agent
        response = orchestrator.process_input(f"/switch {agent_id}")
        
        return {"message": response}
    
    @app.post("/api/interview/switch-mode")
    def switch_mode(
        session_id: str = Query(..., description="Session identifier"),
        mode: str = Query(..., description="Mode to switch to"),
        orchestrator: AgentOrchestrator = Depends(get_orchestrator)
    ):
        """
        Switch the orchestrator mode for a session.
        
        Args:
            session_id: The session identifier
            mode: The mode to switch to
            orchestrator: The orchestrator for the session
            
        Returns:
            Success message
        """
        # Switch mode
        response = orchestrator.process_input(f"/mode {mode}")
        
        return {"message": response}
    
    @app.post("/api/interview/reset")
    def reset_session(
        session_id: str = Query(..., description="Session identifier"),
        orchestrator: AgentOrchestrator = Depends(get_orchestrator)
    ):
        """
        Reset an interview session.
        
        Args:
            session_id: The session identifier
            orchestrator: The orchestrator for the session
            
        Returns:
            Success message
        """
        # Reset session
        response = orchestrator.process_input("/reset")
        
        return {"message": response}
    
    return app 