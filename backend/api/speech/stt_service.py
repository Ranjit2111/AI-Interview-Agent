"""
Speech-to-Text service using Deepgram and AssemblyAI.
"""

import asyncio
import logging
import os
import uuid
from typing import Optional, Dict, Any

from deepgram import DeepgramClient, LiveOptions
from deepgram.clients.live.v1.enums import LiveTranscriptionEvents
from fastapi import WebSocket, WebSocketDisconnect

from .connection_manager import ConnectionManager
from .deepgram_handlers import DeepgramEventHandlers
from .websocket_processor import WebSocketMessageProcessor
from backend.utils.common import get_current_timestamp

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using Deepgram."""
    
    def __init__(self):
        self.deepgram_client = None
        self.connection_manager = ConnectionManager()
        self._initialize_deepgram()
    
    def _initialize_deepgram(self):
        """Initialize Deepgram client."""
        deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY", "")
        
        if not deepgram_api_key:
            logger.warning("DEEPGRAM_API_KEY environment variable not set. Streaming STT service will be unavailable.")
            return
        
        try:
            self.deepgram_client = DeepgramClient(deepgram_api_key)
            logger.info("Successfully initialized Deepgram client.")
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram client: {e}")
    
    def is_available(self) -> bool:
        """Check if STT service is available."""
        return self.deepgram_client is not None
    
    def _create_deepgram_options(self) -> LiveOptions:
        """Create Deepgram live transcription options."""
        return LiveOptions(
            language="en",
            model="nova-2",
            smart_format=True,
            interim_results=True,
            endpointing=True,
            vad_events=True,
            utterance_end_ms="1000",
            # NOTE: Do NOT specify encoding/sample_rate for containerized audio (WebM)
            # Deepgram automatically reads these from the container header
        )
    
    async def _wait_for_connection_active(self, handlers: DeepgramEventHandlers, 
                                        connection_id: str, timeout: int = 10) -> bool:
        """Wait for Deepgram connection to become active."""
        for _ in range(timeout * 10):  # Check every 100ms
            if handlers.connection_active:
                return True
            await asyncio.sleep(0.1)
        
        logger.error("Deepgram connection failed to activate within timeout")
        await self.connection_manager.send_message(
            connection_id,
            {
                "type": "error",
                "error": "Connection timeout - Deepgram failed to connect",
                "timestamp": get_current_timestamp(),
            }
        )
        return False
    
    async def handle_websocket_stream(self, websocket: WebSocket):
        """
        Handle WebSocket streaming for real-time speech-to-text.
        
        Args:
            websocket: FastAPI WebSocket connection
        """
        if not self.is_available():
            await websocket.close(code=1008, reason="Deepgram API key not configured")
            return
        
        connection_id = str(uuid.uuid4())
        await self.connection_manager.connect(connection_id, websocket)
        
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
            await self.connection_manager.send_message(
                connection_id,
                {
                    "type": "connecting",
                    "message": "Validating API key and connecting to Deepgram...",
                    "timestamp": get_current_timestamp(),
                }
            )

            # Create connection to Deepgram with speech detection enabled
            options = self._create_deepgram_options()
            
            # Create a live transcription connection
            deepgram_connection = self.deepgram_client.listen.websocket.v("1")
            
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
                await self.connection_manager.send_message(
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
            processor = WebSocketMessageProcessor(connection_id, self.connection_manager, websocket, message_queue)
            
            # Start the message processor task
            processor_task = asyncio.create_task(processor.process_messages(handlers))
            
            # Wait for connection to become active
            if not await self._wait_for_connection_active(handlers, connection_id):
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
                await self.connection_manager.send_message(
                    connection_id,
                    {
                        "type": "error",
                        "error": str(e),
                        "timestamp": get_current_timestamp(),
                    }
                )
            except Exception:
                # Ignore errors when trying to send error messages
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
            
            self.connection_manager.disconnect(connection_id)
            if deepgram_connection:
                try:
                    deepgram_connection.finish()
                    logger.debug("Deepgram connection closed")
                except Exception as e:
                    logger.error(f"Error finishing Deepgram connection: {e}") 