"""
API endpoints for interacting with the interview agent.
Refactored for multi-session support with database persistence.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import uuid

from fastapi import APIRouter, HTTPException, Depends, Path, Request, Header, Query
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
    final_summary_status: str = "generating"  # 'generating', 'completed', 'error'
    has_immediate_data: bool = True  # Indicates per-turn feedback is immediately available

class FinalSummaryStatusResponse(BaseModel):
    """Response for final summary status check."""
    status: str  # 'generating', 'completed', 'error'
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    suggested_poll_interval: int = 1000  # Milliseconds until next poll (exponential backoff)
    generation_time_estimate: Optional[int] = None  # Estimated remaining time in seconds
    resource_completion_timestamp: Optional[str] = None  # ISO timestamp when resources completed for frontend delay

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

    async def _save_session_async(session_registry: ThreadSafeSessionRegistry, session_id: str, operation: str) -> None:
        """
        FIXED: Async helper to save sessions without blocking request processing.
        
        Args:
            session_registry: The session registry
            session_id: The session ID to save
            operation: The operation that triggered the save (for logging)
        """
        try:
            save_success = await session_registry.save_session(session_id)
            if save_success:
                logger.debug(f"Successfully saved session {session_id} after {operation}")
            else:
                logger.error(f"Failed to save session {session_id} after {operation}")
        except Exception as e:
            logger.exception(f"Error saving session {session_id} after {operation}: {e}")

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
            
            # FIXED: Make database save non-blocking to improve response time
            asyncio.create_task(_save_session_async(session_registry, session_manager.session_id, "start_interview"))
            
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
            
            # FIXED: Make database save non-blocking to improve response time
            asyncio.create_task(_save_session_async(session_registry, session_manager.session_id, "message"))
            
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
        NOTE: This endpoint NEVER returns final summary - frontend must poll /final-summary-status.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Ending session {session_manager.session_id} for user: {user_email}")
        try:
            final_session_results = session_manager.end_interview()
            logger.info(f"Session {session_manager.session_id} ended with results")

            # FIXED: Make database save non-blocking to improve response time
            asyncio.create_task(_save_session_async(session_registry, session_manager.session_id, "end_interview"))

            # FIXED: Return per-turn feedback immediately for instant UX
            # Check if final summary is already available (rare but possible)
            final_summary_status = "generating"
            final_summary_data = {}
            
            if hasattr(session_manager, 'final_summary') and session_manager.final_summary:
                if isinstance(session_manager.final_summary, dict) and "error" in session_manager.final_summary:
                    final_summary_status = "error"
                else:
                    final_summary_status = "completed"
                    final_summary_data = session_manager.final_summary
            
            return EndResponse(
                results=final_summary_data,  # Include final summary if available, empty otherwise
                per_turn_feedback=final_session_results.get("per_turn_feedback", []),
                final_summary_status=final_summary_status,
                has_immediate_data=True
            )

        except Exception as e:
            logger.exception(f"Error ending session {session_manager.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error ending session: {e}")

    @router.get("/final-summary-status", response_model=FinalSummaryStatusResponse)
    async def get_final_summary_status(
        session_manager: AgentSessionManager = Depends(get_session_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
        session_registry: ThreadSafeSessionRegistry = Depends(get_session_registry),
        poll_count: Optional[int] = Query(None, description="Current poll attempt count for exponential backoff")
    ):
        """
        Check the status of final summary generation.
        Requires X-Session-ID header. Authentication is optional.
        NOTE: This is a read-only operation - no session saving needed.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        logger.info(f"Checking final summary status for session {session_manager.session_id} for user: {user_email}")
        try:
            # FIXED: Calculate exponential backoff interval based on poll count
            poll_count = poll_count or 1
            # Exponential backoff: 1s -> 2s -> 4s -> 8s -> max 10s
            suggested_interval = min(1000 * (2 ** min(poll_count - 1, 3)), 10000)
            
            logger.info(f"DEBUG Final Summary Status Check (poll #{poll_count}):")
            logger.info(f"  - Session manager exists: {session_manager is not None}")
            logger.info(f"  - Suggested next poll interval: {suggested_interval}ms")
            
            if session_manager:
                logger.info(f"  - Has final_summary attr: {hasattr(session_manager, 'final_summary')}")
                logger.info(f"  - final_summary value: {session_manager.final_summary}")
                logger.info(f"  - final_summary_generating: {session_manager.final_summary_generating}")
                logger.info(f"  - Session status: {session_manager.session_status}")
                logger.info(f"  - needs_database_save: {getattr(session_manager, 'needs_database_save', False)}")
                
                # CRITICAL FIX: Check if session needs to be saved after final summary completion
                if hasattr(session_manager, 'needs_database_save') and session_manager.needs_database_save:
                    logger.info(f"🔄 Session flagged for database save, saving now...")
                    try:
                        save_success = await session_registry.save_session(session_manager.session_id)
                        if save_success:
                            session_manager.needs_database_save = False  # Clear the flag
                            logger.info(f"✅ Successfully saved session {session_manager.session_id} after final summary completion")
                        else:
                            logger.error(f"❌ Failed to save session {session_manager.session_id} after final summary completion")
                    except Exception as save_error:
                        logger.exception(f"Error saving session after final summary: {save_error}")
            
                # Check if final summary is ready (completed or error)
                if session_manager.final_summary:
                    # FIXED: Check if it's an error dict specifically
                    if isinstance(session_manager.final_summary, dict) and "error" in session_manager.final_summary:
                        # Error occurred during generation
                        error_message = session_manager.final_summary.get("error", "Unknown error")
                        logger.info(f"DEBUG Returning error status: {error_message}")
                        return FinalSummaryStatusResponse(
                            status="error",
                            error=error_message,
                            suggested_poll_interval=suggested_interval
                        )
                    else:
                        # Final summary completed successfully
                        logger.info(f"DEBUG Returning completed status with {len(str(session_manager.final_summary))} chars of data")
                        logger.info(f"DEBUG Final summary data preview: {str(session_manager.final_summary)[:200]}...")
                        # Include resource completion timestamp for frontend delay logic
                        resource_timestamp = None
                        if hasattr(session_manager, 'resource_generation_completed_at') and session_manager.resource_generation_completed_at:
                            resource_timestamp = session_manager.resource_generation_completed_at.isoformat()
                        
                        return FinalSummaryStatusResponse(
                            status="completed",
                            results=session_manager.final_summary,
                            suggested_poll_interval=0,  # No more polling needed
                            resource_completion_timestamp=resource_timestamp
                        )
                else:
                    # Still generating or not started
                    logger.info(f"DEBUG Returning generating status")
                    # FIXED: Add time estimate based on typical generation time (10-45 seconds)
                    time_estimate = max(30 - (poll_count * 2), 5) if poll_count < 15 else 5
                    return FinalSummaryStatusResponse(
                        status="generating",
                        suggested_poll_interval=suggested_interval,
                        generation_time_estimate=time_estimate
                    )
            else:
                logger.error("DEBUG Session manager is None")
                return FinalSummaryStatusResponse(
                    status="error",
                    error="Session manager not found",
                    suggested_poll_interval=suggested_interval
                )

        except Exception as e:
            logger.exception(f"Error checking final summary status for session {session_manager.session_id}: {e}")
            return FinalSummaryStatusResponse(
                status="error",
                error=f"Error checking status: {e}",
                suggested_poll_interval=5000  # Wait 5 seconds before retry on error
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

            # FIXED: Make database save non-blocking to improve response time
            asyncio.create_task(_save_session_async(session_registry, session_manager.session_id, "reset"))

            return ResetResponse(
                message="Session reset successfully",
                session_id=session_manager.session_id
            )

        except Exception as e:
            logger.exception(f"Error resetting session {session_manager.session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error resetting session: {e}")

    app.include_router(router)
    logger.info("Agent API routes registered") 