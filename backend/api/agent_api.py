"""
API endpoints for interacting with the interview agent.
Refactored for single-session mode.
"""

import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Path, Request
from pydantic import BaseModel, Field
from backend.agents.orchestrator import AgentSessionManager
from backend.agents.config_models import SessionConfig
from backend.agents.base import AgentContext
from backend.config import get_logger

logger = get_logger(__name__)

class InterviewStartRequest(BaseModel):
    """Request body for starting/configuring the interview."""
    # Mirror fields from SessionConfig, make them optional to allow partial updates?
    # Or require all for a clean start? Let's require core ones.
    job_role: Optional[str] = Field("General Role", description="Target job role for the interview")
    job_description: Optional[str] = Field(None, description="Job description details")
    resume_content: Optional[str] = Field(None, description="Candidate's resume text")
    style: Optional[str] = Field("formal", description="Interview style (formal, casual, aggressive, technical)")
    difficulty: Optional[str] = Field("medium", description="Interview difficulty level")
    target_question_count: Optional[int] = Field(5, description="Approximate number of questions")
    company_name: Optional[str] = Field(None, description="Company name for context")

class UserInput(BaseModel):
    """Request body for sending user message to the interview."""
    message: str = Field(..., description="The user's message/answer")

class AgentResponse(BaseModel):
    """Standard response structure from agent interactions."""
    role: str
    content: str
    response_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class HistoryResponse(BaseModel):
    """Response for conversation history."""
    history: List[Dict[str, Any]]

class StatsResponse(BaseModel):
    """Response for session statistics."""
    stats: Dict[str, Any]

class ResetResponse(BaseModel):
    """Response for resetting the session."""
    message: str

class EndResponse(BaseModel):
    """Response for ending the interview."""
    results: Dict[str, Any]

def create_agent_api(app):
    """Creates and registers agent API routes."""
    # Update router prefix and tags
    router = APIRouter(prefix="/interview", tags=["interview"])

    @router.post("/start", response_model=ResetResponse)
    async def start_interview(start_request: InterviewStartRequest, request: Request):
        """
        Starts a new interview or configures the existing single session.
        Resets previous state and applies new configuration.
        Returns a simple confirmation message.
        """
        logger.info(f"Received request to start/configure interview: {start_request.dict()}")
        try:
            agent_manager: AgentSessionManager = request.app.state.agent_manager
            if not agent_manager:
                raise HTTPException(status_code=500, detail="Agent Manager not initialized")

            # Create new SessionConfig from request
            # Handle potential None values if needed based on SessionConfig definition
            new_config = SessionConfig(**start_request.dict(exclude_unset=True))

            # Update the singleton agent manager's config
            agent_manager.session_config = new_config
            logger.info(f"Updated agent manager config: {new_config.dict()}")

            # Reset the agent manager's state
            agent_manager.reset_session() # This publishes SESSION_RESET
            logger.info("Agent manager state reset.")

            # Return a simple confirmation message
            return ResetResponse(message=f"Interview session configured and reset for role: {new_config.job_role}")

        except Exception as e:
            logger.exception(f"Error during interview start/config: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to start interview: {e}")

    @router.post("/message", response_model=AgentResponse)
    async def post_message(user_input: UserInput, request: Request):
        """
        Send a user message (answer) to the ongoing interview session.
        Returns the agent's next response (question, feedback, closing).
        """
        logger.info(f"Received user message: '{user_input.message[:50]}...' ")
        try:
            agent_manager: AgentSessionManager = request.app.state.agent_manager
            if not agent_manager:
                raise HTTPException(status_code=500, detail="Agent Manager not initialized")

            # Construct context for the agent
            # History is managed internally by agent_manager after process_message call
            # We just need to trigger the processing of the new message
            # The agent's process method should handle history update and context creation internally now
            agent_response = agent_manager.process_message(message=user_input.message)

            logger.info(f"Agent generated response: {agent_response}")
            return AgentResponse(**agent_response)

        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing message: {e}")

    @router.post("/end", response_model=EndResponse)
    async def end_interview(request: Request):
        """
        Manually ends the current interview session and retrieves final results.
        """
        logger.info("Received request to end interview.")
        try:
            agent_manager: AgentSessionManager = request.app.state.agent_manager
            if not agent_manager:
                raise HTTPException(status_code=500, detail="Agent Manager not initialized")

            # Call the agent manager's end method
            final_results = agent_manager.end_interview()
            logger.info(f"Interview ended. Final results: {final_results}")

            # Note: No database saving happens here anymore
            return EndResponse(results=final_results)

        except Exception as e:
            logger.exception(f"Error ending interview: {e}")
            raise HTTPException(status_code=500, detail=f"Error ending interview: {e}")

    @router.get("/history", response_model=HistoryResponse)
    async def get_history(request: Request):
        """
        Retrieves the conversation history for the current session.
        """
        logger.debug("Received request for conversation history.")
        try:
            agent_manager: AgentSessionManager = request.app.state.agent_manager
            if not agent_manager:
                raise HTTPException(status_code=500, detail="Agent Manager not initialized")

            history = agent_manager.get_conversation_history()
            return HistoryResponse(history=history)

        except Exception as e:
            logger.exception(f"Error retrieving history: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving history: {e}")

    @router.get("/stats", response_model=StatsResponse)
    async def get_stats(request: Request):
        """
        Retrieves performance statistics for the current session.
        """
        logger.debug("Received request for session stats.")
        try:
            agent_manager: AgentSessionManager = request.app.state.agent_manager
            if not agent_manager:
                raise HTTPException(status_code=500, detail="Agent Manager not initialized")

            stats = agent_manager.get_session_stats()
            return StatsResponse(stats=stats)

        except Exception as e:
            logger.exception(f"Error retrieving stats: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving stats: {e}")

    @router.post("/reset", response_model=ResetResponse)
    async def reset_interview(request: Request):
        """
        Resets the state of the single interview session manager.
        """
        logger.info("Received request to reset interview state.")
        try:
            agent_manager: AgentSessionManager = request.app.state.agent_manager
            if not agent_manager:
                raise HTTPException(status_code=500, detail="Agent Manager not initialized")

            agent_manager.reset_session()
            logger.info("Interview state reset successfully.")
            return ResetResponse(message="Interview session state has been reset.")

        except Exception as e:
            logger.exception(f"Error resetting interview state: {e}")
            raise HTTPException(status_code=500, detail=f"Error resetting interview state: {e}")

    # Register the router with the main app
    app.include_router(router)
    logger.info("Agent API router registered with prefix /interview")

# Note: The create_agent_api function now registers the router internally.
# Ensure it's called correctly in main.py. 