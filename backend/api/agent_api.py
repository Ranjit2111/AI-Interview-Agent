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
from backend.services import get_session_manager, get_data_service


class UserMessage(BaseModel):
    """Model for user messages sent to the agent system."""
    message: str = Field(..., description="The user's message text")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")


class InterviewConfig(BaseModel):
    """Model for configuring a new interview session."""
    job_role: str = Field(..., description="Target job role for the interview")
    job_description: str = Field("", description="Detailed job description")
    interview_style: str = Field("FORMAL", description="Style of interview (FORMAL, CASUAL, AGGRESSIVE, TECHNICAL)")
    mode: str = Field(OrchestratorMode.INTERVIEW_WITH_COACHING, description="Operating mode for the orchestrator")
    user_id: Optional[str] = Field(None, description="User identifier")


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str = Field(..., description="Session identifier")
    job_role: str = Field(..., description="Target job role for the interview")
    interview_style: str = Field(..., description="Style of the interview")
    mode: str = Field(..., description="Current orchestrator mode")
    created_at: str = Field(..., description="ISO timestamp of when the session was created")
    active_agent: str = Field(..., description="Currently active agent")


class SessionMetrics(BaseModel):
    """Model for session metrics."""
    total_messages: int = Field(..., description="Total messages in conversation")
    user_message_count: int = Field(..., description="Number of user messages")
    assistant_message_count: int = Field(..., description="Number of assistant messages")
    average_user_message_length: float = Field(..., description="Average length of user messages")
    average_assistant_message_length: float = Field(..., description="Average length of assistant messages")
    average_response_time_seconds: Optional[float] = Field(None, description="Average time between messages in seconds")
    conversation_duration_seconds: Optional[float] = Field(None, description="Total conversation duration in seconds")


class AgentResponse(BaseModel):
    """Model for agent responses."""
    response: str = Field(..., description="The agent's response text")
    session_id: str = Field(..., description="Session identifier")
    agent: str = Field(..., description="Agent that provided the response")
    timestamp: str = Field(..., description="ISO timestamp of the response")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")


def get_session(session_id: str) -> AgentOrchestrator:
    """
    Get an orchestrator instance for a session.
    
    Args:
        session_id: The session identifier
        
    Returns:
        Orchestrator instance
        
    Raises:
        HTTPException: If session not found
    """
    session_manager = get_session_manager()
    orchestrator = session_manager.get_session(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return orchestrator


def create_agent_api(app: FastAPI):
    """
    Create API endpoints for the agent system.
    
    Args:
        app: The FastAPI application
    """
    # Get service instances
    session_manager = get_session_manager()
    data_service = get_data_service()
    
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
        # Create a new session using the session manager
        session_info = session_manager.create_session(
            mode=config.mode,
            job_role=config.job_role,
            job_description=config.job_description,
            interview_style=config.interview_style,
            user_id=config.user_id
        )
        
        # Get the session ID and orchestrator
        session_id = session_info["session_id"]
        orchestrator = session_manager.get_session(session_id)
        
        # Store session in database if user_id provided
        if config.user_id:
            # Persist to database
            session_manager.persist_session(db, session_id)
        
        # Initiate the interview
        welcome_message = orchestrator.process_input("/start")
        
        # Return session info with welcome message
        return {
            **session_info,
            "welcome_message": welcome_message
        }
    
    @app.post("/api/interview/send", response_model=AgentResponse)
    def send_message(
        message: UserMessage,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        orchestrator: AgentOrchestrator = Depends(get_session)
    ):
        """
        Send a message to the interview agent.
        
        Args:
            message: The user's message
            background_tasks: FastAPI background tasks
            db: Database session
            orchestrator: Orchestrator instance
            
        Returns:
            Agent response
        """
        # Process the message
        user_id = message.user_id
        if user_id:
            orchestrator.user_id = user_id
        
        # Process input
        response_text = orchestrator.process_input(message.message, user_id=user_id)
        
        # Schedule background tasks
        background_tasks.add_task(session_manager.persist_session, db, message.session_id)
        
        # Return the response
        return {
            "response": response_text,
            "session_id": message.session_id,
            "agent": orchestrator.active_agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": None
        }
    
    @app.post("/api/interview/end", response_model=Dict[str, Any])
    def end_interview(
        message: UserMessage,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        orchestrator: AgentOrchestrator = Depends(get_session)
    ):
        """
        End an interview session.
        
        Args:
            message: The user's message (session_id required)
            background_tasks: FastAPI background tasks
            db: Database session
            orchestrator: Orchestrator instance
            
        Returns:
            End confirmation and summary
        """
        # Send end command
        end_message = orchestrator.process_input("/end")
        
        # Calculate metrics
        metrics = data_service.calculate_session_metrics(orchestrator.conversation_history)
        
        # Archive the session
        background_tasks.add_task(
            data_service.archive_session, 
            db, 
            message.session_id, 
            orchestrator.conversation_history
        )
        
        # End the session
        background_tasks.add_task(session_manager.end_session, message.session_id)
        
        # Return end confirmation and metrics
        return {
            "message": end_message,
            "session_id": message.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
    
    @app.get("/api/interview/sessions", response_model=List[SessionInfo])
    def list_sessions(user_id: Optional[str] = None):
        """
        List active interview sessions.
        
        Args:
            user_id: Filter by user ID
            
        Returns:
            List of active sessions
        """
        # Get active sessions from session manager
        return session_manager.list_sessions(user_id)
    
    @app.get("/api/interview/info", response_model=SessionInfo)
    def get_session_info(session_id: str = Query(...)):
        """
        Get information about an interview session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Session information
        """
        session_info = session_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return session_info
    
    @app.get("/api/interview/metrics", response_model=SessionMetrics)
    def get_session_metrics(
        session_id: str = Query(...),
        orchestrator: AgentOrchestrator = Depends(get_session)
    ):
        """
        Get metrics for an interview session.
        
        Args:
            session_id: The session identifier
            orchestrator: Orchestrator instance
            
        Returns:
            Session metrics
        """
        # Calculate metrics from conversation history
        return data_service.calculate_session_metrics(orchestrator.conversation_history)
    
    @app.get("/api/interview/history", response_model=List[Dict[str, Any]])
    def get_conversation_history(
        session_id: str = Query(...),
        orchestrator: AgentOrchestrator = Depends(get_session)
    ):
        """
        Get the conversation history for a session.
        
        Args:
            session_id: The session identifier
            orchestrator: Orchestrator instance
            
        Returns:
            List of conversation messages
        """
        # Return the conversation history
        return orchestrator.conversation_history
    
    return app 