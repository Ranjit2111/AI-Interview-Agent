"""
Session-aware Speech API endpoints with database-backed task management and rate limiting.
"""

import os
import tempfile
import logging
import asyncio
import uuid
import random
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form, WebSocket, Depends, Header, Query, WebSocketDisconnect
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel, Field
import jwt

from .speech.stt_service import STTService
from .speech.tts_service import TTSService
from backend.database.db_manager import DatabaseManager
from backend.services.rate_limiting import get_rate_limiter
from backend.services.session_manager import ThreadSafeSessionRegistry
from backend.api.auth_api import get_current_user_optional

logger = logging.getLogger(__name__)

# Global service instances
stt_service = STTService()
tts_service = TTSService()
rate_limiter = get_rate_limiter()


async def get_database_manager() -> DatabaseManager:
    """Dependency to get database manager."""
    from backend.services import get_database_manager
    return get_database_manager()


async def get_session_id_from_header_optional(
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> Optional[str]:
    """Extract session ID from header for speech tasks (optional)."""
    return session_id


async def validate_websocket_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token for WebSocket connections.
    Returns user data if valid, None if invalid.
    """
    try:
        # Get JWT secret - check for mock mode first
        jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
        if not jwt_secret:
            # Check if we're in mock mode
            use_mock_auth = os.environ.get("USE_MOCK_AUTH", "false").lower() == "true"
            if use_mock_auth:
                # Use mock secret for development
                jwt_secret = "development_secret_key_not_for_production"
            else:
                return None
        
        # Decode token
        payload = jwt.decode(
            token, 
            jwt_secret,
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_aud": False  # Disable audience verification for Supabase JWTs
            }
        )
        
        # Check if token has expired
        from datetime import datetime
        if datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow():
            return None
        
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get user from database
        db_manager = await get_database_manager()
        user = await db_manager.get_user(user_id)
        return user
    
    except Exception as e:
        logger.debug(f"WebSocket token validation failed: {e}")
        return None


async def transcribe_audio_assemblyai(audio_file_path: str) -> Dict[str, Any]:
    """
    Core transcription function using AssemblyAI API.
    
    Args:
        audio_file_path: Path to the audio file to transcribe
        
    Returns:
        Dict containing transcription results or error information
    """
    assemblyai_api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
    
    if not assemblyai_api_key:
        raise Exception("AssemblyAI API key not configured")

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Upload file to AssemblyAI
            with open(audio_file_path, 'rb') as f:
                upload_response = await client.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers={"authorization": assemblyai_api_key},
                    files={"file": f}
                )
            
            if upload_response.status_code != 200:
                raise Exception(f"Upload failed: {upload_response.text}")
            
            upload_url = upload_response.json()["upload_url"]
            
            # Request transcription
            transcript_request = {
                "audio_url": upload_url,
                "language_detection": True,
                "punctuate": True,
                "format_text": True
            }
            
            transcript_response = await client.post(
                "https://api.assemblyai.com/v2/transcript",
                headers={"authorization": assemblyai_api_key},
                json=transcript_request,
                timeout=30.0
            )
            
            if transcript_response.status_code != 200:
                raise Exception(f"Transcription request failed: {transcript_response.text}")
            
            transcript_id = transcript_response.json()["id"]
            
            # Poll for completion
            max_poll_attempts = 60  # 5 minutes max
            poll_attempt = 0
            
            while poll_attempt < max_poll_attempts:
                status_response = await client.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers={"authorization": assemblyai_api_key},
                    timeout=30.0
                )
                
                if status_response.status_code != 200:
                    raise Exception(f"Status check failed: {status_response.text}")
                
                result = status_response.json()
                status = result["status"]
                
                if status == "completed":
                    return {
                        "text": result["text"],
                        "confidence": result.get("confidence", 0.0),
                        "language": result.get("language_code", "unknown"),
                        "duration": result.get("audio_duration"),
                        "processing_time": poll_attempt * 5  # Approximate processing time
                    }
                elif status == "error":
                    raise Exception(result.get("error", "Transcription failed"))
                
                poll_attempt += 1
                await asyncio.sleep(5)  # Wait 5 seconds before next check
            
            raise Exception("Transcription timed out after 5 minutes")
            
    except Exception as e:
        logger.error(f"AssemblyAI transcription error: {e}")
        raise


async def transcribe_with_assemblyai_rate_limited(
    audio_file_path: str, 
    task_id: str, 
    session_id: str,
    db_manager: DatabaseManager,
    max_retries: int = 3
):
    """
    Transcribe audio using AssemblyAI with rate limiting and retries.
    
    Args:
        audio_file_path: Path to the audio file
        task_id: Speech task ID for tracking
        session_id: Session ID for context
        db_manager: Database manager for task updates
        max_retries: Maximum number of retries
    """
    try:
        # Update task status to processing
        await db_manager.update_speech_task(
            task_id=task_id,
            status="processing",
            progress_data={"stage": "uploading", "progress": 0}
        )
        
        # Acquire rate limiting slot
        if not await rate_limiter.acquire_assemblyai():
            await db_manager.update_speech_task(
                task_id=task_id,
                status="error",
                error_message="AssemblyAI service temporarily unavailable due to rate limiting"
            )
            return
            
        try:
            # Perform transcription with retries
            transcription_result = None
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    transcription_result = await transcribe_audio_assemblyai(audio_file_path)
                    break  # Success - exit retry loop
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"AssemblyAI attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.2f}s")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"AssemblyAI transcription failed after {max_retries} attempts: {e}")
            
            if transcription_result and "text" in transcription_result:
                # Update task with successful result
                await db_manager.update_speech_task(
                    task_id=task_id,
                    status="completed",
                    result_data={
                        "text": transcription_result["text"],
                        "confidence": transcription_result.get("confidence", 0.0),
                        "language": transcription_result.get("language", "unknown"),
                        "duration": transcription_result.get("duration"),
                        "processing_time": transcription_result.get("processing_time", 0)
                    }
                )
                logger.info(f"Transcription completed for task {task_id}")
            else:
                # Update task with error
                error_msg = f"Transcription failed after {max_retries} attempts"
                if last_error:
                    error_msg += f": {str(last_error)}"
                await db_manager.update_speech_task(
                    task_id=task_id,
                    status="error", 
                    error_message=error_msg
                )
                logger.error(f"Transcription failed for task {task_id}: {error_msg}")
                
        finally:
            # Always release the rate limiting slot
            rate_limiter.release_assemblyai()
            
    except Exception as e:
        # Update task with error
        await db_manager.update_speech_task(
            task_id=task_id,
            status="error",
            error_message=str(e)
        )
        logger.exception(f"Transcription error for task {task_id}: {e}")
        
    finally:
        # Clean up temporary file
        try:
            Path(audio_file_path).unlink(missing_ok=True)
            logger.debug(f"Cleaned up temporary file: {audio_file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {audio_file_path}: {e}")
            
        # ENHANCEMENT: Try to save session state if session is active
        # This ensures speech task results are captured in session context
        try:
            if hasattr(db_manager, '_app_state') and hasattr(db_manager._app_state, 'agent_manager'):
                session_registry = db_manager._app_state.agent_manager
                if session_id in session_registry._active_sessions:
                    save_success = await session_registry.save_session(session_id)
                    if save_success:
                        logger.debug(f"Saved session {session_id} after speech task {task_id} completion")
        except Exception as e:
            logger.debug(f"Could not save session after speech task completion: {e}")


def create_speech_api(app):
    """Creates and registers speech API routes."""
    router = APIRouter(tags=["speech"])

    @router.post("/api/speech-to-text")
    async def speech_to_text(
        background_tasks: BackgroundTasks,
        audio_file: UploadFile = File(...),
        language: str = Form("en-US"),
        session_id: Optional[str] = Depends(get_session_id_from_header_optional),
        db_manager: DatabaseManager = Depends(get_database_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
    ):
        """
        Transcribe uploaded audio file using AssemblyAI with database task tracking.
        Authentication and session ID are optional.
        
        Args:
            audio_file: Audio file to transcribe
            language: Language code (currently ignored - auto-detection used)
            session_id: Optional session ID from header
            
        Returns:
            Task ID for checking transcription status
        """
        user_email = current_user["email"] if current_user else "anonymous"
        
        try:
            logger.info(f"Received speech-to-text request from {user_email}")
            
            # Create task in database first
            task_id = await db_manager.create_speech_task(session_id or "anonymous", "stt_batch")
            
            # Save uploaded file temporarily
            suffix = Path(audio_file.filename or "audio.wav").suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                content = await audio_file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Start background transcription
            background_tasks.add_task(
                transcribe_with_assemblyai_rate_limited,
                temp_file_path,
                task_id,
                session_id or "anonymous",
                db_manager
            )
            
            return JSONResponse({
                "task_id": task_id,
                "message": "Transcription started. Use task_id to check status.",
                "status": "processing"
            })
            
        except Exception as e:
            logger.exception(f"Error processing audio file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")

    @router.get("/api/speech-to-text/status/{task_id}")
    async def check_transcription_status(
        task_id: str,
        session_id: Optional[str] = Depends(get_session_id_from_header_optional),
        db_manager: DatabaseManager = Depends(get_database_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
    ):
        """
        Check the status of a transcription task.
        Authentication and session ID are optional.
        
        Args:
            task_id: Task identifier
            session_id: Optional session ID from header
            
        Returns:
            Task status and results
        """
        user_email = current_user["email"] if current_user else "anonymous"
        
        try:
            task_data = await db_manager.get_speech_task(task_id)
            
            if not task_data:
                raise HTTPException(status_code=404, detail="Task not found")
            
            # Optional session verification - only check if session_id is provided
            if session_id and task_data.get("session_id") != session_id:
                logger.warning(f"Session mismatch for task {task_id}: provided {session_id}, stored {task_data.get('session_id')}")
                # For now, allow access but log the mismatch
            
            response = {
                "task_id": task_id,
                "session_id": task_data.get("session_id"),
                "status": task_data.get("status", "unknown"),
                "created_at": task_data.get("created_at"),
                "updated_at": task_data.get("updated_at")
            }
            
            # Add progress data if available
            if task_data.get("progress_data"):
                response["progress"] = task_data["progress_data"]
            
            # Add results if completed
            if task_data.get("status") == "completed" and task_data.get("result_data"):
                response["result"] = task_data["result_data"]
            
            # Add error if failed
            if task_data.get("status") == "error" and task_data.get("error_message"):
                response["error"] = task_data["error_message"]
            
            return JSONResponse(response)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error retrieving task status for {task_id}")
            raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")

    @router.websocket("/api/speech-to-text/stream")
    async def websocket_stream_endpoint(
        websocket: WebSocket,
        token: Optional[str] = Query(None, description="Optional JWT token for authentication"),
        session_id: Optional[str] = Query(None, description="Optional session ID for linking speech tasks")
    ):
        """
        WebSocket endpoint for real-time speech-to-text streaming with optional authentication.
        Now creates database entries for speech task tracking.
        
        Args:
            websocket: WebSocket connection
            token: Optional JWT token passed as query parameter  
            session_id: Optional session ID for linking speech tasks
        """
        # Optional authentication
        user = None
        if token:
            user = await validate_websocket_token(token)
            logger.info(f"WebSocket STT connection from {'authenticated' if user else 'anonymous'} user")
        else:
            logger.info("WebSocket STT connection from anonymous user")
        
        # Create speech task for tracking this streaming session
        db_manager = await get_database_manager()
        speech_task_id = None
        
        try:
            # Create speech task entry for this streaming session
            speech_task_id = await db_manager.create_speech_task(
                session_id or "anonymous", 
                "stt_stream"
            )
            logger.info(f"Created speech task {speech_task_id} for WebSocket streaming session")
            
            # Update task status to processing
            await db_manager.update_speech_task(
                speech_task_id,
                "processing",
                progress_data={"stage": "streaming", "message": "Real-time transcription active"}
            )
            
            # Handle the actual streaming
            await stt_service.handle_websocket_stream(websocket)
            
            # If we reach here, connection ended normally
            if speech_task_id:
                await db_manager.update_speech_task(
                    speech_task_id,
                    "completed",
                    result_data={"message": "Streaming session completed normally"}
                )
            
        except WebSocketDisconnect:
            logger.debug("WebSocket client disconnected")
            if speech_task_id:
                await db_manager.update_speech_task(
                    speech_task_id,
                    "completed", 
                    result_data={"message": "Client disconnected"}
                )
        except Exception as e:
            logger.exception(f"WebSocket error: {e}")
            if speech_task_id:
                await db_manager.update_speech_task(
                    speech_task_id,
                    "error",
                    error_message=f"WebSocket streaming error: {str(e)}"
                )
            try:
                await websocket.close(code=1011, reason="Internal server error")
            except:
                pass

    @router.post("/api/text-to-speech")
    async def text_to_speech(
        text: str = Form(...),
        voice_id: Optional[str] = Form(None),
        speed: float = Form(1.0, ge=0.5, le=2.0),
    ):
        """
        Convert text to speech using Amazon Polly with rate limiting.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use
            speed: Speech speed
            
        Returns:
            Audio file response
        """
        return await tts_service.synthesize_text(text, voice_id, speed)

    @router.post("/api/text-to-speech/stream")
    async def stream_text_to_speech(
        text: str = Form(...),
        voice_id: Optional[str] = Form(None),
        speed: float = Form(1.0, ge=0.5, le=2.0),
    ):
        """
        Convert text to speech and stream the audio with rate limiting.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use
            speed: Speech speed
            
        Returns:
            Streaming audio response
        """
        return await tts_service.stream_text(text, voice_id, speed)

    @router.get("/api/speech/usage-stats")
    async def get_speech_usage_stats():
        """
        Get current API usage statistics for all speech services.
        
        Returns:
            Usage statistics for AssemblyAI, Polly, and Deepgram
        """
        return JSONResponse(rate_limiter.get_usage_stats())

    # Additional endpoints for new speech task management
    @router.post("/speech/start-task", response_model=SpeechTaskResponse)
    async def start_speech_task(
        task_request: SpeechTaskRequest,
        db_manager: DatabaseManager = Depends(get_database_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
    ):
        """
        Start a new speech processing task.
        Authentication is optional - anonymous users can use speech features.
        """
        user_id = current_user["id"] if current_user else None
        user_email = current_user["email"] if current_user else "anonymous"
        
        try:
            logger.info(f"Starting speech task for user: {user_email}")
            task_id = await db_manager.create_speech_task(
                session_id=task_request.metadata.get("session_id") if task_request.metadata else None,
                task_type=task_request.task_type
            )
            return SpeechTaskResponse(task_id=task_id, status="created")
        except Exception as e:
            logger.exception(f"Error creating speech task: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create speech task: {e}")

    @router.get("/speech/task/{task_id}", response_model=SpeechTaskStatusResponse)
    async def get_speech_task_status(
        task_id: str,
        db_manager: DatabaseManager = Depends(get_database_manager),
        current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
    ):
        """
        Get the status of a speech processing task.
        Authentication is optional.
        """
        user_email = current_user["email"] if current_user else "anonymous"
        try:
            logger.info(f"Getting speech task {task_id} status for user: {user_email}")
            task_data = await db_manager.get_speech_task(task_id)
            if not task_data:
                raise HTTPException(status_code=404, detail="Speech task not found")
            
            return SpeechTaskStatusResponse(
                task_id=task_id,
                status=task_data.get("status", "unknown"),
                result=task_data.get("result_data"),
                error=task_data.get("error_message"),
                created_at=task_data.get("created_at"),
                completed_at=task_data.get("updated_at") if task_data.get("status") == "completed" else None
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error getting speech task status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get task status: {e}")

    app.include_router(router)
    logger.info("Speech API routes registered")


# Pydantic models for speech tasks
class SpeechTaskRequest(BaseModel):
    """Request model for starting a speech task."""
    task_type: str = Field("transcription", description="Type of speech task")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional task metadata")

class SpeechTaskResponse(BaseModel):
    """Response model for speech task creation."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")

class SpeechTaskStatusResponse(BaseModel):
    """Response model for speech task status."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[str] = Field(None, description="Task creation timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp") 