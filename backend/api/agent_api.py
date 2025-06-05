"""
API endpoints for interacting with the interview agent.
Refactored for multi-session support with database persistence.
"""

import logging
from typing import List, Dict, Any, Optional
import uuid

from fastapi import APIRouter, HTTPException, Depends, Path, Request, Header
from pydantic import BaseModel, Field
from backend.agents.orchestrator import AgentSessionManager
from backend.agents.config_models import SessionConfig
from backend.services.session_manager import ThreadSafeSessionRegistry
from backend.api.auth_api import get_current_user, get_current_user_optional
from backend.config import get_logger
from fastapi.responses import JSONResponse

logger = get_logger(__name__)

class InterviewStartRequest(BaseModel):
    """Request body for starting/configuring the interview."""
    job_role: Optional[str] = Field("General Role", description="Target job role for the interview")
    job_description: Optional[str] = Field(None, description="Job description details")
    resume_content: Optional[str] = Field(None, description="Candidate's resume text")
    style: Optional[str] = Field("formal", description="Interview style (formal, casual, aggressive, technical)")
    difficulty: Optional[str] = Field("medium", description="Interview difficulty level")
    target_question_count: Optional[int] = Field(15, description="Approximate number of questions (fallback for question-based)")
    company_name: Optional[str] = Field(None, description="Company name for context")
    interview_duration_minutes: Optional[int] = Field(30, description="Interview duration in minutes (for time-based interviews)")
    use_time_based_interview: Optional[bool] = Field(True, description="Whether to use time-based interview instead of question count")

class UserInput(BaseModel):
    """Request body for sending user message to the interview."""
    message: str = Field(..., description="The user's message/answer")

class AgentResponse(BaseModel):
    """Standard response structure from agent interactions."""
    role: str
    content: Any
    agent: Optional[str] = None
    response_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

class HistoryResponse(BaseModel):
    """Response for conversation history."""
    history: List[Dict[str, Any]]

class StatsResponse(BaseModel):
    """Response for session statistics."""
    stats: Dict[str, Any]

class ResetResponse(BaseModel):
    """Response for resetting the session."""
    message: str
    session_id: Optional[str] = None

class EndResponse(BaseModel):
    """Response for ending the interview."""
    results: Optional[Dict[str, Any]] = None
    per_turn_feedback: Optional[List[Dict[str, str]]] = None

class FinalSummaryStatusResponse(BaseModel):
    """Response for final summary status check."""
    status: str  # 'generating', 'completed', 'error'
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SessionResponse(BaseModel):
    """Response for new session creation."""
    session_id: str
    message: str

# Dependency functions
async def get_session_registry(request: Request) -> ThreadSafeSessionRegistry:
    """Get the session registry from app state."""
    if not hasattr(request.app.state, 'agent_manager'):
        raise HTTPException(status_code=500, detail="Session registry not initialized")
    return request.app.state.agent_manager

async def get_session_id(
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> str:
    """Extract or create session ID from request headers."""
    if session_id:
        return session_id
    else:
        # For backward compatibility, we'll create a session automatically
        # In production, this might require authentication
        raise HTTPException(
            status_code=400, 
            detail="Session ID required. Create a new session first."
        )

async def get_session_manager(
    session_id: str = Depends(get_session_id),
    session_registry: ThreadSafeSessionRegistry = Depends(get_session_registry)
) -> AgentSessionManager:
    """Get session-specific manager."""
    try:
        return await session_registry.get_session_manager(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error getting session manager: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session manager")

def create_agent_api(app):
    """Creates and registers agent API routes."""
    router = APIRouter(prefix="/interview", tags=["interview"])

    @router.post("/session", response_model=SessionResponse)
    async def create_session(
        start_request: InterviewStartRequest,
        session_registry: ThreadSafeSessionRegistry = Depends(get_session_registry),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
    ):
        """
        Create a new interview session with configuration.
        Returns a session ID that must be used in subsequent requests.
        
        Authentication is optional - anonymous users can create sessions.
        """
        user_id = current_user["id"] if current_user else None
        user_email = current_user["email"] if current_user else "anonymous"
        
        logger.info(f"Creating new session for user: {user_email} with config: {start_request.dict()}")
        try:
            # Create SessionConfig from request
            config = SessionConfig(**start_request.dict(exclude_unset=True))
            
            # Create new session with optional user ID
            session_id = await session_registry.create_new_session(
                user_id=user_id,
                initial_config=config
            )
            
            logger.info(f"Created new session: {session_id} for user: {user_email}")
            return SessionResponse(
                session_id=session_id,
                message=f"Session created for role: {config.job_role}"
            )

        except Exception as e:
            logger.exception(f"Error creating session: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create session: {e}")

    @router.post("/start", response_model=AgentResponse)
    async def start_interview(
        start_request: InterviewStartRequest,
        session_manager: AgentSessionManager = Depends(get_session_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
        session_registry: ThreadSafeSessionRegistry = Depends(get_session_registry)
    ):
        """
        Configure an existing session, reset its state, and return the initial introduction message.
        Requires X-Session-ID header. Authentication is optional.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Configuring session {session_manager.session_id} for user: {user_email} with: {start_request.dict()}")
        try:
            # Create new SessionConfig from request
            new_config = SessionConfig(**start_request.dict(exclude_unset=True))

            # Update the session manager's config
            session_manager.session_config = new_config
            logger.info(f"Updated session config: {new_config.dict()}")

            # Reset the session state
            session_manager.reset_session()
            logger.info("Session state reset.")

            # Get the initial introduction message from the interviewer agent
            # Pass empty message to trigger initialization/introduction phase
            initial_response = session_manager.process_message(message="")
            logger.info(f"Generated initial introduction for session {session_manager.session_id}")
            
            # CRITICAL FIX: Save session state to database after processing
            save_success = await session_registry.save_session(session_manager.session_id)
            if not save_success:
                logger.error(f"Failed to save session {session_manager.session_id} after start_interview")
            else:
                logger.debug(f"Successfully saved session {session_manager.session_id} after start_interview")
            
            # Debug logging to track message processing
            logger.info(f"DEBUG - Initial response structure: {initial_response}")
            logger.info(f"DEBUG - Response type: {type(initial_response)}")
            logger.info(f"DEBUG - Response keys: {list(initial_response.keys()) if isinstance(initial_response, dict) else 'Not a dict'}")
            logger.info(f"DEBUG - Content value: {initial_response.get('content', 'NO CONTENT FIELD')}")
            logger.info(f"DEBUG - Content type: {type(initial_response.get('content', None))}")

            return initial_response

        except Exception as e:
            logger.exception(f"Error configuring session: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to configure session: {e}")

    @router.post("/message", response_model=AgentResponse)
    async def post_message(
        user_input: UserInput,
        session_manager: AgentSessionManager = Depends(get_session_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
        session_registry: ThreadSafeSessionRegistry = Depends(get_session_registry)
    ):
        """
        Send a user message to the interview session.
        Requires X-Session-ID header. Authentication is optional.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Session {session_manager.session_id} received message from {user_email}: '{user_input.message[:50]}...'")
        try:
            interviewer_response_dict = session_manager.process_message(message=user_input.message)
            logger.info(f"Session {session_manager.session_id} generated response")
            
            # CRITICAL FIX: Save session state to database after processing message
            save_success = await session_registry.save_session(session_manager.session_id)
            if not save_success:
                logger.error(f"Failed to save session {session_manager.session_id} after processing message")
                # Don't fail the request, but log the error
            else:
                logger.debug(f"Successfully saved session {session_manager.session_id} after processing message")
            
            return interviewer_response_dict

        except Exception as e:
            logger.exception(f"Error processing message in session {session_manager.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing message: {e}")

    @router.post("/end", response_model=EndResponse)
    async def end_interview(
        session_manager: AgentSessionManager = Depends(get_session_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
        session_registry: ThreadSafeSessionRegistry = Depends(get_session_registry)
    ):
        """
        End the interview session and retrieve final results.
        Requires X-Session-ID header. Authentication is optional.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Ending session {session_manager.session_id} for user: {user_email}")
        try:
            final_session_results = session_manager.end_interview()
            logger.info(f"Session {session_manager.session_id} ended with results")

            # CRITICAL FIX: Save session state to database after ending interview
            save_success = await session_registry.save_session(session_manager.session_id)
            if not save_success:
                logger.error(f"Failed to save session {session_manager.session_id} after ending interview")
            else:
                logger.debug(f"Successfully saved session {session_manager.session_id} after ending interview")

            return EndResponse(
                results=final_session_results.get("coaching_summary") or {},
                per_turn_feedback=final_session_results.get("per_turn_feedback", [])
            )

        except Exception as e:
            logger.exception(f"Error ending session {session_manager.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error ending session: {e}")

    @router.get("/final-summary-status", response_model=FinalSummaryStatusResponse)
    async def get_final_summary_status(
        session_manager: AgentSessionManager = Depends(get_session_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
        session_registry: ThreadSafeSessionRegistry = Depends(get_session_registry)
    ):
        """
        Check the status of final summary generation.
        Requires X-Session-ID header. Authentication is optional.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Checking final summary status for session {session_manager.session_id} for user: {user_email}")
        try:
            logger.info(f"DEBUG Final Summary Status Check:")
            logger.info(f"  - Session manager exists: {session_manager is not None}")
            
            if session_manager:
                logger.info(f"  - Has final_summary attr: {hasattr(session_manager, 'final_summary')}")
                logger.info(f"  - final_summary value: {session_manager.final_summary}")
                logger.info(f"  - final_summary_generating: {session_manager.final_summary_generating}")
                logger.info(f"  - Session status: {session_manager.session_status}")
                
                # Check if final summary is ready (completed or error)
                if session_manager.final_summary:
                    if isinstance(session_manager.final_summary, dict) and "error" in session_manager.final_summary:
                        # Error occurred during generation
                        logger.info(f"DEBUG Returning error status: {session_manager.final_summary.get('error')}")
                        return FinalSummaryStatusResponse(
                            status="error",
                            error=session_manager.final_summary.get("error")
                        )
                    else:
                        # Final summary completed successfully
                        logger.info(f"DEBUG Returning completed status with {len(str(session_manager.final_summary))} chars of data")
                        logger.info(f"DEBUG Final summary data preview: {str(session_manager.final_summary)[:200]}...")
                        return FinalSummaryStatusResponse(
                            status="completed",
                            results=session_manager.final_summary
                        )
                else:
                    # Still generating or not started
                    logger.info(f"DEBUG Returning generating status")

            # CRITICAL FIX: Always save session state during status check to ensure latest changes are persisted
            save_success = await session_registry.save_session(session_manager.session_id)
            if save_success:
                logger.debug(f"✅ Successfully saved session {session_manager.session_id} during status check")
            else:
                logger.error(f"❌ Failed to save session {session_manager.session_id} during status check")
            
            return FinalSummaryStatusResponse(
                status="generating"
            )

        except Exception as e:
            logger.exception(f"Error checking final summary status for session {session_manager.session_id}: {e}")
            return FinalSummaryStatusResponse(
                status="error",
                error=f"Error checking status: {e}"
            )

    @router.get("/history", response_model=HistoryResponse)
    async def get_history(
        session_manager: AgentSessionManager = Depends(get_session_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
    ):
        """
        Get conversation history for the session.
        Requires X-Session-ID header. Authentication is optional.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Getting history for session {session_manager.session_id} for user: {user_email}")
        try:
            return HistoryResponse(
                history=session_manager.get_conversation_history()
            )

        except Exception as e:
            logger.exception(f"Error getting history for session {session_manager.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting conversation history: {e}")

    @router.get("/stats", response_model=StatsResponse)
    async def get_stats(
        session_manager: AgentSessionManager = Depends(get_session_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
    ):
        """
        Get statistics for the session.
        Requires X-Session-ID header. Authentication is optional.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Getting stats for session {session_manager.session_id} for user: {user_email}")
        try:
            return StatsResponse(
                stats=session_manager.get_session_stats()
            )

        except Exception as e:
            logger.exception(f"Error getting stats for session {session_manager.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting session stats: {e}")

    @router.get("/per-turn-feedback", response_model=List[Dict[str, str]])
    async def get_per_turn_feedback(
        session_manager: AgentSessionManager = Depends(get_session_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
    ):
        """
        Get current per-turn coaching feedback for the session.
        Requires X-Session-ID header. Authentication is optional.
        This endpoint allows real-time access to coaching feedback as it's generated.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Getting per-turn feedback for session {session_manager.session_id} for user: {user_email}")
        try:
            return session_manager.per_turn_coaching_feedback_log

        except Exception as e:
            logger.exception(f"Error getting per-turn feedback for session {session_manager.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting per-turn feedback: {e}")

    @router.post("/reset", response_model=ResetResponse)
    async def reset_interview(
        session_manager: AgentSessionManager = Depends(get_session_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
        session_registry: ThreadSafeSessionRegistry = Depends(get_session_registry)
    ):
        """
        Reset the session state.
        Requires X-Session-ID header. Authentication is optional.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Resetting session {session_manager.session_id} for user: {user_email}")
        try:
            session_manager.reset_session()
            logger.info(f"Session {session_manager.session_id} reset")

            # CRITICAL FIX: Save session state to database after reset
            save_success = await session_registry.save_session(session_manager.session_id)
            if not save_success:
                logger.error(f"Failed to save session {session_manager.session_id} after reset")
            else:
                logger.debug(f"Successfully saved session {session_manager.session_id} after reset")

            return ResetResponse(
                message="Session reset successfully",
                session_id=session_manager.session_id
            )

        except Exception as e:
            logger.exception(f"Error resetting session {session_manager.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error resetting session: {e}")

    app.include_router(router)
    logger.info("Agent API routes registered") 