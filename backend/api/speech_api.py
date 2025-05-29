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

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form, WebSocket, Depends, Header
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel, Field

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

router = APIRouter()


async def get_database_manager() -> DatabaseManager:
    """Dependency to get database manager."""
    from backend.services import get_database_manager
    return get_database_manager()


async def get_session_id_from_header_optional(
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> Optional[str]:
    """Extract session ID from header for speech tasks (optional)."""
    return session_id


async def transcribe_with_assemblyai_rate_limited(
    audio_file_path: str, 
    task_id: str, 
    session_id: str,
    db_manager: DatabaseManager,
    max_retries: int = 3
):
    """
    Transcribe audio using AssemblyAI API with rate limiting and retry logic.
    
    Args:
        audio_file_path: Path to the audio file
        task_id: Unique task identifier
        session_id: Session ID for database storage
        db_manager: Database manager instance
        max_retries: Maximum retry attempts
    """
    assemblyai_api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
    
    if not assemblyai_api_key:
        await db_manager.update_speech_task(
            task_id, 
            "error", 
            error_message="AssemblyAI API key not configured"
        )
        return

    # Acquire rate limiting slot
    if not await rate_limiter.acquire_assemblyai():
        await db_manager.update_speech_task(
            task_id,
            "error",
            error_message="AssemblyAI service temporarily unavailable due to rate limiting"
        )
        return

    try:
        await db_manager.update_speech_task(
            task_id, 
            "processing", 
            progress_data={"step": "uploading", "message": "Uploading audio..."}
        )
        
        for attempt in range(max_retries):
            try:
                # Upload file to AssemblyAI
                async with httpx.AsyncClient(timeout=300.0) as client:
                    with open(audio_file_path, 'rb') as f:
                        upload_response = await client.post(
                            "https://api.assemblyai.com/v2/upload",
                            headers={"authorization": assemblyai_api_key},
                            files={"file": f}
                        )
                    
                    if upload_response.status_code != 200:
                        raise HTTPException(
                            status_code=upload_response.status_code, 
                            detail=f"Upload failed: {upload_response.text}"
                        )
                    
                    upload_url = upload_response.json()["upload_url"]
                    
                    await db_manager.update_speech_task(
                        task_id, 
                        "processing", 
                        progress_data={"step": "transcribing", "message": "Starting transcription..."}
                    )
                    
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
                        raise HTTPException(
                            status_code=transcript_response.status_code,
                            detail=f"Transcription request failed: {transcript_response.text}"
                        )
                    
                    transcript_id = transcript_response.json()["id"]
                    await db_manager.update_speech_task(
                        task_id, 
                        "processing", 
                        progress_data={"step": "processing", "message": "Transcription in progress...", "transcript_id": transcript_id}
                    )
                    
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
                            raise HTTPException(
                                status_code=status_response.status_code,
                                detail=f"Status check failed: {status_response.text}"
                            )
                        
                        result = status_response.json()
                        status = result["status"]
                        
                        if status == "completed":
                            await db_manager.update_speech_task(
                                task_id,
                                "completed",
                                result_data={
                                    "transcription": result["text"],
                                    "confidence": result.get("confidence", 0.0),
                                    "language": result.get("language_code", "unknown"),
                                    "duration": result.get("audio_duration")
                                }
                            )
                            return
                        elif status == "error":
                            await db_manager.update_speech_task(
                                task_id,
                                "error",
                                error_message=result.get("error", "Transcription failed")
                            )
                            return
                        
                        poll_attempt += 1
                        await asyncio.sleep(5)  # Wait 5 seconds before next check
                    
                    if poll_attempt >= max_poll_attempts:
                        await db_manager.update_speech_task(
                            task_id,
                            "error",
                            error_message="Transcription timed out after 5 minutes"
                        )
                    return
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"AssemblyAI attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.exception(f"AssemblyAI transcription error for task {task_id}")
                    await db_manager.update_speech_task(
                        task_id,
                        "error",
                        error_message=f"Transcription failed after {max_retries} attempts: {str(e)}"
                    )
                    return
                    
    finally:
        # Always release the rate limiting slot
        rate_limiter.release_assemblyai()
        
        # Clean up uploaded file
        try:
            if os.path.exists(audio_file_path):
                os.unlink(audio_file_path)
        except Exception as e:
            logger.error(f"Failed to clean up audio file {audio_file_path}: {e}")


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
    Convert uploaded audio file to text using AssemblyAI with session-aware task management.
    Authentication and session ID are optional.
    
    Args:
        audio_file: Audio file to transcribe
        language: Language code for transcription
        session_id: Optional session ID from header
        
    Returns:
        Task ID for checking transcription status
    """
    user_email = current_user["email"] if current_user else "anonymous"
    
    # Check if AssemblyAI service is available
    if not rate_limiter.is_api_available('assemblyai'):
        raise HTTPException(
            status_code=429,
            detail="AssemblyAI service temporarily unavailable. Please try again later."
        )
    
    try:
        task_id = str(uuid.uuid4())
        logger.info(f"Starting transcription task {task_id} for user: {user_email}")
        
        # Create task in database (with or without session)
        await db_manager.create_speech_task(
            task_id=task_id,
            user_id=current_user["id"] if current_user else None,
            session_id=session_id,
            task_type="transcription",
            status="created"
        )
        
        # Save uploaded file temporarily
        temp_file_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(await audio_file.read())
            temp_file_path = temp_file.name
        
        # Start background transcription
        background_tasks.add_task(
            transcribe_with_assemblyai_rate_limited, 
            temp_file_path, 
            task_id, 
            session_id,
            db_manager
        )
        
        return JSONResponse({
            "task_id": task_id,
            "session_id": session_id,
            "status": "processing",
            "message": "Transcription started. Use the task_id to check status."
        })
        
    except Exception as e:
        logger.exception("Error starting speech-to-text transcription")
        raise HTTPException(status_code=500, detail=f"Failed to start transcription: {str(e)}")


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
async def websocket_stream_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time speech-to-text streaming with rate limiting.
    """
    await stt_service.handle_websocket_stream(websocket)


@router.post("/api/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("Matthew"),
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
    voice_id: str = Form("Matthew"),
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


def create_speech_api(app):
    """Creates and registers speech API routes."""
    router = APIRouter(prefix="/speech", tags=["speech"])

    @router.post("/start-task", response_model=SpeechTaskResponse)
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
                user_id=user_id,
                audio_data=task_request.audio_data,
                task_type=task_request.task_type,
                metadata=task_request.metadata
            )
            return SpeechTaskResponse(task_id=task_id, status="created")
        except Exception as e:
            logger.exception(f"Error creating speech task: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create speech task: {e}")

    @router.get("/task/{task_id}", response_model=SpeechTaskStatusResponse)
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
                result=task_data.get("result"),
                error=task_data.get("error"),
                created_at=task_data.get("created_at"),
                completed_at=task_data.get("completed_at")
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
    audio_data: str = Field(..., description="Base64 encoded audio data")
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