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
import html

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form, Query
from fastapi.responses import JSONResponse, StreamingResponse, Response
import httpx
import boto3 
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError # Added for AWS Polly

logger = logging.getLogger(__name__)

ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY", "")


AWS_REGION = os.environ.get("AWS_REGION")
polly_client = None

if AWS_REGION:
    try:
        polly_client = boto3.client(
            "polly",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        logger.info(f"Successfully initialized AWS Polly client in region {AWS_REGION}.")
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error(f"AWS credentials not found or incomplete. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY. Error: {e}")
        polly_client = None # Ensure client is None if initialization fails
    except ClientError as e:
        logger.error(f"AWS ClientError initializing Polly client: {e}. Check AWS permissions and region.")
        polly_client = None
    except Exception as e:
        logger.error(f"Failed to initialize AWS Polly client: {e}")
        polly_client = None # Ensure client is None for any other init error
else:
    logger.warning("AWS_REGION environment variable not set. AWS Polly TTS service will be unavailable.")


speech_tasks = {}

router = APIRouter()

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
                file_content = f.read() # Read the content first
                response = await client.post(
                    "https://api.assemblyai.com/v2/upload",
                    headers=headers,
                    data=file_content # Pass the bytes
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
                    logger.info(f"Transcription completed with text: '{data['text']}'")
                    speech_tasks[task_id] = {
                        "status": "completed",
                        "transcript": data["text"]
                    }
                    return
                elif data["status"] == "error":
                    logger.error(f"Transcription error: {data.get('error', 'Unknown error')}")
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
    finally:
        # Ensure temporary file is always deleted
        if audio_file_path and os.path.exists(audio_file_path):
            try:
                os.unlink(audio_file_path)
                logger.info(f"Cleaned up temporary STT file: {audio_file_path}")
            except OSError as e:
                logger.error(f"Error deleting temporary STT file {audio_file_path}: {e}")


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
    Get a list of available TTS voices from the Amazon Polly.

    Returns:
        JSON response with voice list or error message.
    """
    if not polly_client:
        raise HTTPException(
            status_code=503,
            detail="TTS service (Amazon Polly) not configured or unavailable. Check AWS_REGION and credentials."
        )

    try:
        response = await asyncio.to_thread(polly_client.describe_voices)
        # response = polly_client.describe_voices() # If not in async context or FastAPI handles it
        
        formatted_voices = []
        if response and 'Voices' in response:
            for voice in response['Voices']:
                formatted_voices.append({
                    "id": voice.get("Id", "unknown_voice"),
                    "name": voice.get("Name", "Unknown Voice"),
                    "language": voice.get("LanguageCode", "unknown"),
                    "description": f"{voice.get('Gender', 'Unknown gender')} voice. Engine(s): {', '.join(voice.get('SupportedEngines', []))}",
                    "gender": voice.get("Gender", "unknown").lower()
                })
        
        if not formatted_voices:
             logger.warning("No voices returned from Polly or response format unexpected.")
             # Provide a default or raise error, consistent with old behavior (provides default)
             # For Polly, it's better to be accurate if service is up but no voices listed.
             # However, to maintain a similar fallback for UI if it expects *something*:
             formatted_voices = [{
                 "id": "Matthew", # Example Polly Voice ID
                 "name": "Default Voice (Matthew)",
                 "language": "en-US",
                 "description": "Default voice (if API response was empty or failed to parse)",
                 "gender": "male"
             }]
             # If API call was successful but no voices, it's an issue.
             # If call itself failed, earlier error handling would catch it.

        return JSONResponse({"voices": formatted_voices})

    except ClientError as e:
        logger.error(f"Error contacting Amazon Polly for voices: {e}")
        raise HTTPException(
            status_code=getattr(e.response, 'get', lambda x, y: y)('Error', {}).get('Code', 503), # Try to get AWS error code
            detail=f"Amazon Polly service error: {e.response.get('Error', {}).get('Message', str(e))}"
        )
    except Exception as e:
        logger.exception("Unexpected error getting TTS voices from Polly")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/api/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("Matthew"),  # Default Polly voice (e.g., Matthew for en-US)
    speed: float = Form(1.0, ge=0.5, le=2.0), # Speed control via SSML
):
    """
    Synthesize speech from text using Amazon Polly.

    Args:
        text: Text to synthesize.
        voice_id: ID (name) of the Polly voice to use (e.g., 'Matthew').
        speed: Speech speed (0.5 to 2.0), converted to SSML prosody rate.

    Returns:
        Audio data as an MP3 file response.
    """
    if not polly_client:
        raise HTTPException(
            status_code=503,
            detail="TTS service (Amazon Polly) not configured or unavailable. Check AWS_REGION and credentials."
        )

    escaped_text = html.escape(text)
    
    # SSML for speed control. Polly rate is percentage.
    # "medium" is default (100%). "slow" ~85%, "x-slow" ~70%. "fast" ~120%, "x-fast" ~150%.
    # We can map the float speed to a percentage.
    speed_percentage = int(speed * 100)
    ssml_text = f'<speak><prosody rate="{speed_percentage}%">{escaped_text}</prosody></speak>'
    
    logger.info(f"Sending TTS request to Amazon Polly with voice: {voice_id}, speed: {speed} ({speed_percentage}%)")



    try:
        response = await asyncio.to_thread(
            polly_client.synthesize_speech,
            Text=ssml_text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            TextType="ssml",
            Engine="neural" # Or 'neural' if preferred and voice supports it
        )
        
        audio_stream = response.get("AudioStream")
        if audio_stream:
            audio_content = audio_stream.read()
            audio_stream.close() # Important to close the stream
            return Response(content=audio_content, media_type="audio/mpeg")
        else:
            logger.error(f"No AudioStream in Polly response: {response}")
            raise HTTPException(status_code=500, detail="TTS server returned no audio data.")

    except ClientError as e:
        error_code = getattr(e.response, 'get', lambda x, y: y)('Error', {}).get('Code', 500)
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Amazon Polly service error during synthesis: {error_code} - {error_message}")
        raise HTTPException(
            status_code=int(error_code) if isinstance(error_code, str) and error_code.isdigit() else 503,
            detail=f"Amazon Polly service error: {error_message}"
        )
    except Exception as e:
        logger.exception("Unexpected error during text-to-speech synthesis with Polly")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/api/text-to-speech/stream")
async def stream_text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("Matthew"),  # Default Polly voice
    speed: float = Form(1.0, ge=0.5, le=2.0),
):
    """
    Synthesize speech from text using Amazon Polly and stream the audio.

    Args:
        text: Text to synthesize.
        voice_id: ID (name) of the voice to use.
        speed: Speech speed (0.5 to 2.0), converted to SSML prosody rate.

    Returns:
        StreamingResponse containing MP3 audio data.
    """
    if not polly_client:
        raise HTTPException(
            status_code=503,
            detail="TTS service (Amazon Polly) not configured or unavailable. Check AWS_REGION and credentials."
        )

    escaped_text = html.escape(text)
    speed_percentage = int(speed * 100)
    ssml_text = f'<speak><prosody rate="{speed_percentage}%">{escaped_text}</prosody></speak>'

    logger.info(f"Sending Streaming TTS request to Amazon Polly with voice: {voice_id}, speed: {speed} ({speed_percentage}%)")
    
    try:
        # boto3's synthesize_speech is blocking, so run in thread for async handler
        # However, its AudioStream is iterable, suitable for StreamingResponse
        response = await asyncio.to_thread(
            polly_client.synthesize_speech,
            Text=ssml_text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            TextType="ssml",
            Engine="standard" # Or 'neural'
        )

        audio_stream = response.get("AudioStream")

        if not audio_stream:
            logger.error(f"No AudioStream in Polly streaming response: {response}")
            raise HTTPException(status_code=500, detail="TTS server returned no audio data for streaming.")

        async def generator(stream):
            try:
                for chunk in stream:
                    yield chunk
            finally:
                stream.close() # Ensure stream is closed

        return StreamingResponse(generator(audio_stream), media_type="audio/mpeg")

    except ClientError as e:
        error_code = getattr(e.response, 'get', lambda x, y: y)('Error', {}).get('Code', 500)
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Amazon Polly service error during streaming synthesis: {error_code} - {error_message}")
        # If error occurs before streaming starts, this is fine.
        # If error occurs *during* streaming, client might get partial response then error.
        # Boto3's stream is typically read fully by `synthesize_speech` before this point,
        # unless OutputFormat='pcm' then streamed. For 'mp3', it's usually delivered as a whole.
        # The `StreamingBody` itself is an iterator over chunks of the already synthesized speech.
        raise HTTPException(
            status_code=int(error_code) if isinstance(error_code, str) and error_code.isdigit() else 503,
            detail=f"Amazon Polly service error: {error_message}"
        )
    except Exception as e:
        logger.exception("Unexpected error during streaming text-to-speech synthesis with Polly")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def create_speech_api(app):
    """
    Create speech processing API endpoints.
    
    Args:
        app: FastAPI application
    """
    app.include_router(router) 