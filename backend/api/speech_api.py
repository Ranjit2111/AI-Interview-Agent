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
import json
from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse, Response
from starlette.websockets import WebSocketState
import httpx
import boto3 
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

# Import Deepgram for streaming STT
from deepgram import (
    DeepgramClient,
    LiveOptions
)
from deepgram.clients.live.v1.enums import LiveTranscriptionEvents

# Import our utility function for consistent timestamps
from backend.utils.common import get_current_timestamp

logger = logging.getLogger(__name__)
load_dotenv()
# API Keys for different STT services
ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY", "")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")

# AWS Polly setup for TTS
AWS_REGION = os.environ.get("AWS_REGION")
polly_client = None

# Initialize Deepgram client
deepgram_client = None
if DEEPGRAM_API_KEY:
    try:
        # Initialize with API key only as per latest SDK docs
        deepgram_client = DeepgramClient(DEEPGRAM_API_KEY)
        logger.info("Successfully initialized Deepgram client.")
    except Exception as e:
        logger.error(f"Failed to initialize Deepgram client: {e}")
        deepgram_client = None
else:
    logger.warning("DEEPGRAM_API_KEY environment variable not set. Streaming STT service will be unavailable.")

# Initialize Amazon Polly client
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
        polly_client = None
    except ClientError as e:
        logger.error(f"AWS ClientError initializing Polly client: {e}. Check AWS permissions and region.")
        polly_client = None
    except Exception as e:
        logger.error(f"Failed to initialize AWS Polly client: {e}")
        polly_client = None
else:
    logger.warning("AWS_REGION environment variable not set. AWS Polly TTS service will be unavailable.")


speech_tasks = {}

router = APIRouter()

# Websocket connection manager for streaming STT
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, connection_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connection {connection_id} established")

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            # Don't need to close explicitly as FastAPI handles this
            del self.active_connections[connection_id]
            logger.info(f"WebSocket connection {connection_id} closed")

    async def send_message(self, connection_id: str, message: Dict[str, Any]):
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except RuntimeError as e:
                logger.error(f"Error sending message to WebSocket {connection_id}: {e}")
                self.disconnect(connection_id)

# Create a connection manager instance
manager = ConnectionManager()


class DeepgramEventHandlers:
    """Handles Deepgram WebSocket event callbacks."""
    
    def __init__(self, message_queue: asyncio.Queue, current_loop: asyncio.AbstractEventLoop):
        self.message_queue = message_queue
        self.current_loop = current_loop
        self.connection_active = False
    
    def _queue_message(self, message_data: Dict[str, Any]) -> None:
        """Safely queue messages from sync event handlers to async context."""
        try:
            self.current_loop.call_soon_threadsafe(self.message_queue.put_nowait, message_data)
        except Exception as e:
            logger.error(f"Error queuing message from event handler: {e}")
    
    def on_open(self, self_param, open_event, **kwargs):
        """Handle Deepgram connection open."""
        self.connection_active = True
        logger.debug("Deepgram connection opened successfully")
        self._queue_message({
            "type": "connected",
            "message": "Ready to receive audio",
            "timestamp": get_current_timestamp(),
        })
    
    def on_message(self, self_param, result, **kwargs):
        """Handle transcript messages from Deepgram."""
        try:
            sentence = result.channel.alternatives[0].transcript
            is_final = result.is_final
            
            # Only log significant transcripts to reduce noise
            if sentence and (is_final or len(sentence) > 10):
                logger.debug(f"Transcript: '{sentence}' (Final: {is_final})")
            
            # Queue the transcription results to be sent to the client
            if sentence is not None:  # Send even empty strings to maintain flow
                self._queue_message({
                    "type": "transcript",
                    "text": sentence,
                    "is_final": is_final,
                    "timestamp": get_current_timestamp(),
                })
            else:
                logger.warning("Received transcript result with None text")
                
        except Exception as e:
            logger.error(f"Error in transcript handler: {e}")
    
    def on_speech_started(self, self_param, speech_started, **kwargs):
        """Handle speech start detection."""
        try:
            logger.debug("Speech started detected")
            self._queue_message({
                "type": "speech_started",
                "timestamp": get_current_timestamp(),
            })
        except Exception as e:
            logger.error(f"Error in speech started handler: {e}")
    
    def on_utterance_end(self, self_param, utterance_end, **kwargs):
        """Handle utterance end detection."""
        try:
            logger.debug("Utterance end detected")
            self._queue_message({
                "type": "utterance_end",
                "timestamp": get_current_timestamp(),
            })
        except Exception as e:
            logger.error(f"Error in utterance end handler: {e}")
    
    def on_error(self, self_param, error, **kwargs):
        """Handle Deepgram errors."""
        self.connection_active = False
        logger.error(f"Deepgram error: {error}")
        self._queue_message({
            "type": "error",
            "error": str(error),
            "timestamp": get_current_timestamp(),
        })
    
    def on_close(self, self_param, close_event, **kwargs):
        """Handle Deepgram connection close."""
        self.connection_active = False
        logger.debug("Deepgram connection closed")
        self._queue_message({
            "type": "disconnected",
            "message": "Deepgram connection closed",
            "timestamp": get_current_timestamp(),
        })
    
    def on_metadata(self, self_param, metadata, **kwargs):
        """Handle Deepgram metadata."""
        logger.debug("Received metadata from Deepgram")
        self._queue_message({
            "type": "metadata",
            "metadata": metadata,
            "timestamp": get_current_timestamp(),
        })
    
    def on_unhandled(self, self_param, unhandled, **kwargs):
        """Handle unhandled Deepgram events."""
        logger.debug(f"Unhandled event from Deepgram: {unhandled}")


class WebSocketMessageProcessor:
    """Processes messages between Deepgram and WebSocket client."""
    
    def __init__(self, connection_id: str, manager: ConnectionManager, 
                 websocket: WebSocket, message_queue: asyncio.Queue):
        self.connection_id = connection_id
        self.manager = manager
        self.websocket = websocket
        self.message_queue = message_queue
    
    async def process_messages(self, handlers: DeepgramEventHandlers) -> None:
        """Process messages from the sync event handlers and send them via WebSocket."""
        while handlers.connection_active and self.websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                # Wait for a message from the queue (with timeout to check connection status)
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                
                # Send the message to the WebSocket client
                await self.manager.send_message(self.connection_id, message)
                
                # Mark the message as processed
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                # No message received in timeout period - continue to check connection status
                continue
            except Exception as e:
                logger.error(f"Error processing message from queue: {e}")
                break
    
    async def handle_audio_streaming(self, deepgram_connection, handlers: DeepgramEventHandlers) -> None:
        """Handle streaming audio data from WebSocket to Deepgram."""
        while handlers.connection_active and self.websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                # Receive audio chunks with a timeout
                audio_data = await asyncio.wait_for(self.websocket.receive_bytes(), timeout=5.0)
                
                # Only send data if connection is active
                if handlers.connection_active and deepgram_connection:
                    try:
                        deepgram_connection.send(audio_data)
                    except Exception as e:
                        logger.error(f"Error sending audio to Deepgram: {e}")
                        handlers.connection_active = False
                        break
                
            except asyncio.TimeoutError:
                # No audio data received in the timeout period - this is normal
                # Continue and let the SDK handle keep-alive
                continue
            except WebSocketDisconnect:
                logger.info(f"WebSocket client {self.connection_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                await self.manager.send_message(
                    self.connection_id,
                    {
                        "type": "error",
                        "error": f"Error processing audio: {str(e)}",
                        "timestamp": get_current_timestamp(),
                    }
                )
                break


def _create_deepgram_options() -> LiveOptions:
    """Create Deepgram LiveOptions with the required configuration."""
    return LiveOptions(
        language="en",
        model="nova-2",  # Use the latest Nova-2 model
        smart_format=True,
        interim_results=True,
        endpointing=True,
        vad_events=True,  # Enable Voice Activity Detection events
        utterance_end_ms="1000",  # Wait 1 second of silence before finalizing an utterance
        filler_words=True,  # Enable transcription of filler words (uh, um, ahh, etc.)
        # NOTE: Do NOT specify encoding and sample_rate for containerized audio (WebM)
        # Deepgram will automatically read these from the container header
    )


async def _wait_for_connection_active(handlers: DeepgramEventHandlers, 
                                      connection_id: str, manager: ConnectionManager) -> bool:
    """Wait for Deepgram connection to become active with timeout."""
    # Wait up to 15 seconds for the connection to become active  
    for i in range(30):  # 30 * 0.5s = 15s
        if handlers.connection_active:
            return True
        await asyncio.sleep(0.5)
        if i % 10 == 0:  # Log every 5 seconds
            logger.debug(f"Still waiting for Deepgram connection... ({i//2}s)")
    
    logger.error("Deepgram connection failed to open within timeout period")
    await manager.send_message(
        connection_id,
        {
            "type": "error",
            "error": "Failed to establish Deepgram connection within timeout period. Check API key and network connectivity.",
            "timestamp": get_current_timestamp(),
        }
    )
    return False


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
                logger.debug(f"Cleaned up temporary STT file: {audio_file_path}")
            except OSError as e:
                logger.error(f"Error deleting temporary STT file {audio_file_path}: {e}")


@router.post("/api/speech-to-text")
async def speech_to_text(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    language: str = Form("en-US")
):
    """
    Convert speech audio to text using batch processing (AssemblyAI).
    
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


@router.websocket("/api/speech-to-text/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time speech-to-text streaming using Deepgram.
    
    The client sends binary audio data and receives transcription results in real-time.
    """
    if not deepgram_client:
        await websocket.close(code=1008, reason="Deepgram API key not configured")
        return
    
    connection_id = str(uuid.uuid4())
    await manager.connect(connection_id, websocket)
    
    # Track connection state
    deepgram_connection = None
    
    # Create a thread-safe queue to pass messages from sync event handlers to async context
    message_queue = asyncio.Queue()
    
    # Get the current event loop for thread-safe communication
    current_loop = asyncio.get_running_loop()
    
    try:
        # Log API key status (without revealing the actual key)
        logger.debug(f"Starting Deepgram connection for client {connection_id}")

        # Send connecting status to client
        await manager.send_message(
            connection_id,
            {
                "type": "connecting",
                "message": "Validating API key and connecting to Deepgram...",
                "timestamp": get_current_timestamp(),
            }
        )

        # Create connection to Deepgram with speech detection enabled
        options = _create_deepgram_options()
        
        # Create a live transcription connection
        deepgram_connection = deepgram_client.listen.websocket.v("1")
        
        # Create event handlers
        handlers = DeepgramEventHandlers(message_queue, current_loop)
            
        # Register all event handlers
        deepgram_connection.on(LiveTranscriptionEvents.Open, handlers.on_open)
        deepgram_connection.on(LiveTranscriptionEvents.Transcript, handlers.on_message)  
        deepgram_connection.on(LiveTranscriptionEvents.SpeechStarted, handlers.on_speech_started)
        deepgram_connection.on(LiveTranscriptionEvents.UtteranceEnd, handlers.on_utterance_end)
        deepgram_connection.on(LiveTranscriptionEvents.Error, handlers.on_error)
        deepgram_connection.on(LiveTranscriptionEvents.Close, handlers.on_close)
        deepgram_connection.on(LiveTranscriptionEvents.Metadata, handlers.on_metadata)
        deepgram_connection.on(LiveTranscriptionEvents.Unhandled, handlers.on_unhandled)
        
        # Start the connection
        logger.debug("Starting Deepgram connection...")
        
        if not deepgram_connection.start(options):
            logger.error("Failed to start Deepgram connection")
            await manager.send_message(
                connection_id,
                {
                    "type": "error",
                    "error": "Failed to start Deepgram connection",
                    "timestamp": get_current_timestamp(),
                }
            )
            return
            
        logger.debug("Deepgram connection start initiated - waiting for open event")
        
        # Create message processor
        processor = WebSocketMessageProcessor(connection_id, manager, websocket, message_queue)
        
        # Start the message processor task
        processor_task = asyncio.create_task(processor.process_messages(handlers))
        
        # Wait for connection to become active
        if not await _wait_for_connection_active(handlers, connection_id, manager):
            return
            
        logger.debug("Deepgram connection established and active")
        
        # Start receiving and forwarding audio data
        await processor.handle_audio_streaming(deepgram_connection, handlers)
    
    except WebSocketDisconnect:
        logger.debug(f"WebSocket client {connection_id} disconnected")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        try:
            # Try to send error to client
            await manager.send_message(
                connection_id,
                {
                    "type": "error",
                    "error": str(e),
                    "timestamp": get_current_timestamp(),
                }
            )
        except:
            pass
    finally:
        # Clean up
        if 'handlers' in locals():
            handlers.connection_active = False
        
        # Cancel the message processor task
        if 'processor_task' in locals():
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                pass
        
        # Clean up the message queue
        while not message_queue.empty():
            try:
                message_queue.get_nowait()
                message_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        manager.disconnect(connection_id)
        if deepgram_connection:
            try:
                deepgram_connection.finish()
                logger.debug("Deepgram connection closed")
            except Exception as e:
                logger.error(f"Error finishing Deepgram connection: {e}")


def _prepare_tts_ssml(text: str, speed: float) -> str:
    """Prepare SSML text for TTS synthesis."""
    escaped_text = html.escape(text)
    speed_percentage = int(speed * 100)
    
    # Add a brief initial pause using <break> tag to prevent the first words from being cut off
    return f'<speak><break time="250ms"/><prosody rate="{speed_percentage}%">{escaped_text}</prosody></speak>'


async def _synthesize_speech(ssml_text: str, voice_id: str) -> bytes:
    """Synthesize speech using Amazon Polly."""
    response = await asyncio.to_thread(
        polly_client.synthesize_speech,
        Text=ssml_text,
        OutputFormat="mp3",
        VoiceId=voice_id,
        TextType="ssml",
        Engine="generative"
    )
    
    audio_stream = response.get("AudioStream")
    if not audio_stream:
        raise HTTPException(status_code=500, detail="TTS server returned no audio data.")
    
    try:
        audio_content = audio_stream.read()
        return audio_content
    finally:
        audio_stream.close()


@router.post("/api/text-to-speech")
async def text_to_speech(
    text: str = Form(...),
    voice_id: str = Form("Matthew"),  # Always use Matthew as default voice
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

    ssml_text = _prepare_tts_ssml(text, speed)
    
    logger.debug(f"TTS request: voice={voice_id}, speed={speed}")

    try:
        audio_content = await _synthesize_speech(ssml_text, voice_id)
        return Response(content=audio_content, media_type="audio/mpeg")

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
    voice_id: str = Form("Matthew"),  # Always use Matthew as default voice
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

    ssml_text = _prepare_tts_ssml(text, speed)
    
    logger.debug(f"Streaming TTS request: voice={voice_id}, speed={speed}")
    
    try:
        # boto3's synthesize_speech is blocking, so run in thread for async handler
        # However, its AudioStream is iterable, suitable for StreamingResponse
        response = await asyncio.to_thread(
            polly_client.synthesize_speech,
            Text=ssml_text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            TextType="ssml",
            Engine="generative"
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
                stream.close()

        return StreamingResponse(generator(audio_stream), media_type="audio/mpeg")

    except ClientError as e:
        error_code = getattr(e.response, 'get', lambda x, y: y)('Error', {}).get('Code', 500)
        error_message = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"Amazon Polly service error during streaming synthesis: {error_code} - {error_message}")
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