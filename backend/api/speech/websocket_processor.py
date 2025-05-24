"""
WebSocket message processor for handling audio streaming.
"""

import asyncio
import logging
from typing import TYPE_CHECKING
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

if TYPE_CHECKING:
    from .connection_manager import ConnectionManager
    from .deepgram_handlers import DeepgramEventHandlers

logger = logging.getLogger(__name__)


class WebSocketMessageProcessor:
    """Processes WebSocket messages and handles audio streaming."""
    
    def __init__(self, connection_id: str, manager: 'ConnectionManager', 
                 websocket: WebSocket, message_queue: asyncio.Queue):
        self.connection_id = connection_id
        self.manager = manager
        self.websocket = websocket
        self.message_queue = message_queue
    
    async def process_messages(self, handlers: 'DeepgramEventHandlers') -> None:
        """Process messages from the queue and send to WebSocket client."""
        try:
            while handlers.connection_active:
                try:
                    # Get message from queue with timeout
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
                    await self.manager.send_message(self.connection_id, message)
                    self.message_queue.task_done()
                except asyncio.TimeoutError:
                    # No message in queue, continue
                    continue
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    break
        except Exception as e:
            logger.error(f"Error in message processor: {e}")
    
    async def handle_audio_streaming(self, deepgram_connection, handlers: 'DeepgramEventHandlers') -> None:
        """Handle incoming audio data and forward to Deepgram."""
        try:
            while handlers.connection_active:
                if self.websocket.client_state == WebSocketState.DISCONNECTED:
                    logger.debug("WebSocket client disconnected")
                    break
                
                try:
                    # Receive audio data from client
                    audio_data = await self.websocket.receive_bytes()
                    
                    # Forward to Deepgram
                    if deepgram_connection and handlers.connection_active:
                        deepgram_connection.send(audio_data)
                    
                except WebSocketDisconnect:
                    logger.debug("WebSocket disconnected during audio streaming")
                    break
                except Exception as e:
                    logger.error(f"Error handling audio data: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in audio streaming handler: {e}")
        finally:
            handlers.connection_active = False 