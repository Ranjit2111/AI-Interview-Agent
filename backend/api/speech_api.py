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
from fastapi.responses import JSONResponse, StreamingResponse, Response
import httpx

# Optional TTS dependency - Install with backend/setup_kokoro_tts.py
# If missing, TTS features will be disabled but the API will still work
# try:
#     from kokoro_tts_fastapi_client import KokoroClient, Voice # REMOVED old client
# except ImportError:
#     KokoroClient = None # REMOVED old client
#     Voice = None # REMOVED old client

logger = logging.getLogger(__name__)

# Check for AssemblyAI API key
ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY", "")

# Kokoro TTS API URL (running locally, set by setup_kokoro_tts.py)
KOKORO_API_URL = os.environ.get("KOKORO_API_URL") # Removed default, should be set by setup

# Dictionary to store speech processing tasks
speech_tasks = {}

# Create router
router = APIRouter()

# Shared httpx client for TTS requests
tts_client = httpx.AsyncClient(timeout=60.0) # Increased timeout for potentially long synthesis

# Helper to check TTS service health
async def is_tts_service_available():
    if not KOKORO_API_URL:
        logger.warning("KOKORO_API_URL environment variable is not set. TTS service is disabled.")
        return False
    try:
        response = await tts_client.get(f"{KOKORO_API_URL}/health")
        response.raise_for_status() # Raise exception for 4xx or 5xx status codes
        logger.info("Kokoro TTS service is healthy.")
        return True
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.error(f"Kokoro TTS service check failed: {e}")
        return False

# Initialize Kokoro TTS client # REMOVED old initialization block
# kokoro_client = None
# try:
#     kokoro_client = KokoroClient(base_url=KOKORO_API_URL)
#     logger.info("Successfully initialized Kokoro TTS client")
# except Exception as e:
#     logger.warning(f"Failed to initialize Kokoro TTS client: {e}")

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
    Get a list of available TTS voices from the Kokoro server.

    Returns:
        JSON response with voice list or error message.
    """
    if not KOKORO_API_URL:
        raise HTTPException(
            status_code=503,
            detail="TTS service URL not configured. Set KOKORO_API_URL environment variable."
        )

    try:
        response = await tts_client.get(f"{KOKORO_API_URL}/voices")
        response.raise_for_status()
        voices_data = response.json() # Should be a list of dicts

        # Map the response to the format expected by the frontend (if different)
        # Assuming frontend expects 'id', 'name', 'language', 'description'
        # The server provides 'name', 'language', 'description' currently.
        # We can use 'name' as 'id' for now.
        formatted_voices = [
            {
                "id": voice.get("name", "unknown_voice"), # Use name as ID
                "name": voice.get("name", "Unknown Voice"),
                "language": voice.get("language", "unknown"),
                "description": voice.get("description", "No description available"),
                "gender": voice.get("gender", "unknown") # Add gender if server provides it later
            }
            for voice in voices_data
        ]

        return JSONResponse({"voices": formatted_voices})

    except httpx.RequestError as e:
        logger.error(f"Error contacting TTS service for voices: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"TTS service unavailable: {e}"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Error response from TTS service for voices: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"TTS service error: {e.response.text}"
        )
    except Exception as e:
        logger.exception("Unexpected error getting TTS voices")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/api/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("af_heart"),  # Default voice matches server default
    speed: float = Form(1.0, ge=0.5, le=2.0), # Added validation from server
    # pitch: float = Form(1.0), # REMOVED - Not supported by server
    # format: str = Form("mp3") # REMOVED - Server returns WAV
):
    """
    Synthesize speech from text using the Kokoro TTS server.

    Args:
        text: Text to synthesize.
        voice_id: ID (name) of the voice to use (e.g., 'af_heart').
        speed: Speech speed (0.5 to 2.0).

    Returns:
        Audio data as a WAV file response.
    """
    if not KOKORO_API_URL:
        raise HTTPException(
            status_code=503,
            detail="TTS service URL not configured. Set KOKORO_API_URL environment variable."
        )

    payload = {
        "text": text,
        "voice": voice_id,
        "speed": speed
    }
    logger.info(f"Sending TTS request to {KOKORO_API_URL}/synthesize with voice: {voice_id}, speed: {speed}")

    try:
        response = await tts_client.post(f"{KOKORO_API_URL}/synthesize", json=payload)
        response.raise_for_status() # Check for 4xx/5xx errors

        # Check content type (should be audio/wav)
        content_type = response.headers.get("content-type")
        if content_type != "audio/wav":
            logger.error(f"Unexpected content type from TTS server: {content_type}. Response: {response.text}")
            raise HTTPException(
                status_code=500,
                detail=f"TTS server returned unexpected content type: {content_type}"
            )

        # Return the raw audio data with the correct content type
        return Response(content=response.content, media_type="audio/wav")

    except httpx.RequestError as e:
        logger.error(f"Error contacting TTS service for synthesis: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"TTS service unavailable: {e}"
        )
    except httpx.HTTPStatusError as e:
        error_detail = f"TTS service error: {e.response.text}"
        try:
            # Attempt to parse JSON error detail from server
            error_json = e.response.json()
            error_detail = error_json.get("detail", error_detail)
        except json.JSONDecodeError:
            pass # Use raw text if not JSON
        logger.error(f"Error response from TTS service for synthesis: {e.response.status_code} - {error_detail}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.exception("Unexpected error during text-to-speech synthesis")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Optional: Consider removing or adapting this streaming endpoint if true streaming isn't implemented/needed.
# For now, it will behave like the non-streaming endpoint.
@router.post("/api/text-to-speech/stream")
async def stream_text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("af_heart"),  # Default voice
    speed: float = Form(1.0, ge=0.5, le=2.0),
    # pitch: float = Form(1.0) # REMOVED
):
    """
    Synthesize speech from text and stream the audio (currently returns full WAV).

    Args:
        text: Text to synthesize.
        voice_id: ID (name) of the voice to use.
        speed: Speech speed (0.5 to 2.0).

    Returns:
        StreamingResponse containing WAV audio data.
    """
    # This implementation currently mirrors the non-streaming version
    # because the custom server returns the full WAV at once.
    # A true streaming implementation would require server-side changes
    # and different handling here (iterating over response chunks).
    if not KOKORO_API_URL:
        raise HTTPException(
            status_code=503,
            detail="TTS service URL not configured. Set KOKORO_API_URL environment variable."
        )

    payload = {
        "text": text,
        "voice": voice_id,
        "speed": speed
    }
    logger.info(f"Sending Streaming TTS request to {KOKORO_API_URL}/synthesize with voice: {voice_id}, speed: {speed}")

    try:
        # Use a context manager for the request to ensure resources are cleaned up
        async with tts_client.stream("POST", f"{KOKORO_API_URL}/synthesize", json=payload) as response:
            response.raise_for_status()

            content_type = response.headers.get("content-type")
            if content_type != "audio/wav":
                 logger.error(f"Unexpected content type from TTS streaming endpoint: {content_type}.")
                 # Need to read the error response body if possible
                 error_body = await response.aread()
                 raise HTTPException(
                     status_code=500,
                     detail=f"TTS server returned unexpected content type '{content_type}': {error_body.decode()}"
                 )

            # Stream the response content
            # Although the server sends it all at once now, this structure
            # allows for future true streaming if the server is updated.
            async def generator():
                async for chunk in response.aiter_bytes():
                    yield chunk

            return StreamingResponse(generator(), media_type="audio/wav")

    except httpx.RequestError as e:
        logger.error(f"Error contacting TTS service for streaming synthesis: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"TTS service unavailable: {e}"
        )
    except httpx.HTTPStatusError as e:
        error_detail = f"TTS service error"
        try:
            # Attempt to read error detail from the response body
            error_body = await e.response.aread()
            error_detail = error_body.decode()
            # Try parsing JSON detail if possible
            try:
                 error_json = json.loads(error_detail)
                 error_detail = error_json.get("detail", error_detail)
            except json.JSONDecodeError:
                 pass # Use raw text if not JSON
        except Exception:
             pass # Ignore if reading body fails

        logger.error(f"Error response from TTS service for streaming synthesis: {e.response.status_code} - {error_detail}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=error_detail
        )
    except Exception as e:
        logger.exception("Unexpected error during streaming text-to-speech synthesis")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def create_speech_api(app):
    """
    Create speech processing API endpoints.
    
    Args:
        app: FastAPI application
    """
    app.include_router(router) 