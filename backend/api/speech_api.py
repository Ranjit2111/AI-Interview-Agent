"""
Refactored Speech API endpoints.
Clean, modular implementation using extracted services.
"""

import os
import tempfile
import logging
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form, WebSocket
from fastapi.responses import JSONResponse
import httpx

from .speech.stt_service import STTService
from .speech.tts_service import TTSService

logger = logging.getLogger(__name__)

# Global service instances
stt_service = STTService()
tts_service = TTSService()

# Task storage for async operations
speech_tasks: Dict[str, Dict[str, Any]] = {}

router = APIRouter()


async def transcribe_with_assemblyai(audio_file_path: str, task_id: str):
    """
    Transcribe audio using AssemblyAI API.
    
    Args:
        audio_file_path: Path to the audio file
        task_id: Unique task identifier
    """
    assemblyai_api_key = os.environ.get("ASSEMBLYAI_API_KEY", "")
    
    if not assemblyai_api_key:
        speech_tasks[task_id] = {
            "status": "error",
            "error": "AssemblyAI API key not configured"
        }
        return

    try:
        speech_tasks[task_id] = {"status": "processing", "progress": "Uploading audio..."}
        
        # Upload file to AssemblyAI
        async with httpx.AsyncClient() as client:
            with open(audio_file_path, 'rb') as f:
                upload_response = await client.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers={"authorization": assemblyai_api_key},
                    files={"file": f},
                    timeout=300.0
                )
            
            if upload_response.status_code != 200:
                raise HTTPException(status_code=upload_response.status_code, 
                                  detail=f"Upload failed: {upload_response.text}")
            
            upload_url = upload_response.json()["upload_url"]
            
            speech_tasks[task_id]["progress"] = "Starting transcription..."
            
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
                raise HTTPException(status_code=transcript_response.status_code,
                                  detail=f"Transcription request failed: {transcript_response.text}")
            
            transcript_id = transcript_response.json()["id"]
            speech_tasks[task_id]["progress"] = "Transcription in progress..."
            
            # Poll for completion
            max_attempts = 60  # 5 minutes max
            attempt = 0
            
            while attempt < max_attempts:
                status_response = await client.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers={"authorization": assemblyai_api_key},
                    timeout=30.0
                )
                
                if status_response.status_code != 200:
                    raise HTTPException(status_code=status_response.status_code,
                                      detail=f"Status check failed: {status_response.text}")
                
                result = status_response.json()
                status = result["status"]
                
                if status == "completed":
                    speech_tasks[task_id] = {
                        "status": "completed",
                        "transcription": result["text"],
                        "confidence": result.get("confidence", 0.0),
                        "language": result.get("language_code", "unknown")
                    }
                    break
                elif status == "error":
                    speech_tasks[task_id] = {
                        "status": "error",
                        "error": result.get("error", "Transcription failed")
                    }
                    break
                
                attempt += 1
                await asyncio.sleep(5)  # Wait 5 seconds before next check
            
            if attempt >= max_attempts:
                speech_tasks[task_id] = {
                    "status": "error",
                    "error": "Transcription timed out"
                }
                
    except Exception as e:
        logger.exception(f"AssemblyAI transcription error for task {task_id}")
        speech_tasks[task_id] = {
            "status": "error",
            "error": str(e)
        }
    finally:
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
    language: str = Form("en-US")
):
    """
    Convert uploaded audio file to text using AssemblyAI.
    
    Args:
        audio_file: Audio file to transcribe
        language: Language code for transcription
        
    Returns:
        Task ID for checking transcription status
    """
    import uuid
    import asyncio
    
    task_id = str(uuid.uuid4())
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Start background transcription
        background_tasks.add_task(transcribe_with_assemblyai, temp_file_path, task_id)
        
        return JSONResponse({
            "task_id": task_id,
            "status": "processing",
            "message": "Transcription started. Use the task_id to check status."
        })
        
    except Exception as e:
        logger.exception("Error starting speech-to-text transcription")
        raise HTTPException(status_code=500, detail=f"Failed to start transcription: {str(e)}")


@router.get("/api/speech-to-text/status/{task_id}")
async def check_transcription_status(task_id: str):
    """
    Check the status of a transcription task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Task status and results
    """
    if task_id not in speech_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = speech_tasks[task_id]
    
    # Clean up completed/failed tasks after returning results
    if task["status"] in ["completed", "error"]:
        # Return the task but don't delete it immediately
        # Let the client decide when to clean up
        pass
    
    return JSONResponse(task)


@router.websocket("/api/speech-to-text/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time speech-to-text streaming using Deepgram.
    """
    await stt_service.handle_websocket_stream(websocket)


@router.post("/api/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("Matthew"),
    speed: float = Form(1.0, ge=0.5, le=2.0),
):
    """
    Synthesize speech from text using Amazon Polly.
    
    Args:
        text: Text to synthesize
        voice_id: Voice to use for synthesis
        speed: Speech speed (0.5 to 2.0)
        
    Returns:
        Audio data as MP3
    """
    return await tts_service.synthesize_text(text, voice_id, speed)


@router.post("/api/text-to-speech/stream")
async def stream_text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("Matthew"),
    speed: float = Form(1.0, ge=0.5, le=2.0),
):
    """
    Synthesize speech from text and stream the audio.
    
    Args:
        text: Text to synthesize
        voice_id: Voice to use for synthesis
        speed: Speech speed (0.5 to 2.0)
        
    Returns:
        Streaming audio response
    """
    return await tts_service.stream_text(text, voice_id, speed)


def create_speech_api(app):
    """
    Create speech processing API endpoints.
    
    Args:
        app: FastAPI application
    """
    app.include_router(router) 