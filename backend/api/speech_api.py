"""
API endpoints for speech processing.
Includes Speech-to-Text and Text-to-Speech functionality.
"""

import os
import uuid
import tempfile
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
import asyncio
import json

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
from kokoro_tts_fastapi_client import KokoroClient, Voice

logger = logging.getLogger(__name__)

# Check for AssemblyAI API key
ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY", "")

# Kokoro TTS API URL (running locally)
KOKORO_API_URL = os.environ.get("KOKORO_API_URL", "http://localhost:8008")

# Dictionary to store speech processing tasks
speech_tasks = {}

# Create router
router = APIRouter()

# Initialize Kokoro TTS client
kokoro_client = None
try:
    kokoro_client = KokoroClient(base_url=KOKORO_API_URL)
    logger.info("Successfully initialized Kokoro TTS client")
except Exception as e:
    logger.warning(f"Failed to initialize Kokoro TTS client: {e}")

async def transcribe_with_assemblyai(audio_file_path: str, task_id: str):
    """
    Transcribe an audio file using AssemblyAI.
    
    Args:
        audio_file_path: Path to the audio file
        task_id: Unique ID for this transcription task
    """
    if not ASSEMBLYAI_API_KEY:
        speech_tasks[task_id] = {
            "status": "error",
            "error": "AssemblyAI API key not configured"
        }
        return
    
    # Upload the audio file
    try:
        # Update task status
        speech_tasks[task_id] = {"status": "uploading"}
        
        headers = {
            "authorization": ASSEMBLYAI_API_KEY
        }
        
        async with httpx.AsyncClient() as client:
            # Upload the file
            with open(audio_file_path, "rb") as f:
                response = await client.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers=headers,
                    data=f
                )
            
            if response.status_code != 200:
                speech_tasks[task_id] = {
                    "status": "error",
                    "error": f"Failed to upload file: {response.text}"
                }
                return
            
            upload_url = response.json()["upload_url"]
            
            # Start transcription
            speech_tasks[task_id] = {"status": "transcribing"}
            
            response = await client.post(
                "https://api.assemblyai.com/v2/transcript",
                json={"audio_url": upload_url},
                headers=headers
            )
            
            if response.status_code != 200:
                speech_tasks[task_id] = {
                    "status": "error",
                    "error": f"Failed to start transcription: {response.text}"
                }
                return
            
            transcript_id = response.json()["id"]
            
            # Poll for completion
            while True:
                await asyncio.sleep(2)
                response = await client.get(
                    f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    speech_tasks[task_id] = {
                        "status": "error",
                        "error": f"Failed to check transcription status: {response.text}"
                    }
                    return
                
                data = response.json()
                
                if data["status"] == "completed":
                    speech_tasks[task_id] = {
                        "status": "completed",
                        "transcript": data["text"]
                    }
                    return
                elif data["status"] == "error":
                    speech_tasks[task_id] = {
                        "status": "error",
                        "error": f"Transcription error: {data.get('error', 'Unknown error')}"
                    }
                    return
                
                # Still processing
                speech_tasks[task_id]["status"] = "transcribing"
    
    except Exception as e:
        logger.exception("Error in AssemblyAI transcription")
        speech_tasks[task_id] = {
            "status": "error",
            "error": f"Transcription error: {str(e)}"
        }


@router.post("/api/speech-to-text")
async def speech_to_text(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    language: str = Form("en-US")
):
    """
    Convert speech audio to text.
    
    Args:
        background_tasks: FastAPI background tasks
        audio_file: Audio file to transcribe
        language: Language code
        
    Returns:
        JSON response with task_id for polling or transcript if processing was quick
    """
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    
    # Create a temporary file
    temp_dir = Path(tempfile.gettempdir())
    audio_path = temp_dir / f"speech_{task_id}{os.path.splitext(audio_file.filename)[1]}"
    
    # Save the uploaded file
    with open(audio_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)
    
    # Start transcription in background
    background_tasks.add_task(transcribe_with_assemblyai, str(audio_path), task_id)
    
    # Return task ID for polling
    return JSONResponse({
        "task_id": task_id,
        "status": "processing"
    })


@router.get("/api/speech-to-text/status/{task_id}")
async def check_transcription_status(task_id: str):
    """
    Check the status of a speech-to-text task.
    
    Args:
        task_id: ID of the task to check
        
    Returns:
        JSON response with task status and transcript if completed
    """
    if task_id not in speech_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = speech_tasks[task_id]
    
    if task["status"] == "completed":
        # Clean up the task data after successful retrieval
        transcript = task["transcript"]
        
        # Remove task to save memory (optional)
        # del speech_tasks[task_id]
        
        return JSONResponse({
            "status": "completed",
            "transcript": transcript
        })
    
    return JSONResponse(task)


@router.get("/api/text-to-speech/voices")
async def get_available_voices():
    """
    Get a list of available TTS voices.
    
    Returns:
        JSON response with available voices
    """
    if not kokoro_client:
        raise HTTPException(status_code=503, detail="Text-to-speech service is not available")
    
    try:
        voices = await kokoro_client.list_voices()
        return JSONResponse({
            "voices": [
                {
                    "id": voice.id,
                    "name": voice.name,
                    "language": voice.language,
                    "gender": voice.gender
                }
                for voice in voices
            ]
        })
    except Exception as e:
        logger.exception("Failed to get TTS voices")
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {str(e)}")


@router.post("/api/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("en_female_1"),  # Default voice
    speed: float = Form(1.0),
    pitch: float = Form(1.0),
    format: str = Form("mp3")
):
    """
    Convert text to speech using Kokoro TTS.
    
    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use
        speed: Speech speed (0.5-2.0)
        pitch: Speech pitch (0.5-2.0)
        format: Audio format (mp3, wav)
        
    Returns:
        Streaming response with audio data
    """
    if not kokoro_client:
        raise HTTPException(status_code=503, detail="Text-to-speech service is not available")
    
    try:
        # Get voice by ID
        voices = await kokoro_client.list_voices()
        voice = next((v for v in voices if v.id == voice_id), None)
        
        if not voice:
            raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
        
        # Generate audio
        audio_bytes = await kokoro_client.generate_speech(
            text=text,
            voice=voice,
            speed=speed,
            pitch=pitch
        )
        
        # Return audio as streaming response
        return StreamingResponse(
            content=iter([audio_bytes]),
            media_type=f"audio/{format}",
            headers={
                "Content-Disposition": f"attachment; filename=speech_{uuid.uuid4()}.{format}"
            }
        )
    except Exception as e:
        logger.exception("Failed to generate speech")
        raise HTTPException(status_code=500, detail=f"Failed to generate speech: {str(e)}")


@router.post("/api/text-to-speech/stream")
async def stream_text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("en_female_1"),  # Default voice
    speed: float = Form(1.0),
    pitch: float = Form(1.0)
):
    """
    Stream text to speech using Kokoro TTS with word-level timestamps.
    
    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use
        speed: Speech speed (0.5-2.0)
        pitch: Speech pitch (0.5-2.0)
        
    Returns:
        Streaming response with audio data and timestamps
    """
    if not kokoro_client:
        raise HTTPException(status_code=503, detail="Text-to-speech service is not available")
    
    try:
        # Get voice by ID
        voices = await kokoro_client.list_voices()
        voice = next((v for v in voices if v.id == voice_id), None)
        
        if not voice:
            raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
        
        # Generate captioned speech
        result = await kokoro_client.generate_captioned_speech(
            text=text,
            voice=voice,
            speed=speed,
            pitch=pitch
        )
        
        # Return audio with timestamp data
        return JSONResponse({
            "audio_base64": result.audio_base64,
            "timestamps": result.timestamps,
            "duration": result.duration
        })
    except Exception as e:
        logger.exception("Failed to stream speech")
        raise HTTPException(status_code=500, detail=f"Failed to stream speech: {str(e)}")


def create_speech_api(app):
    """
    Create speech processing API endpoints.
    
    Args:
        app: FastAPI application
    """
    app.include_router(router) 