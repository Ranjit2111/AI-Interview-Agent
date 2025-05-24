"""
Deepgram WebSocket event handlers for speech-to-text streaming.
"""

import asyncio
import logging
from typing import Dict, Any

from backend.utils.common import get_current_timestamp

logger = logging.getLogger(__name__)


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
        """Handle metadata from Deepgram."""
        try:
            logger.debug(f"Received metadata: {metadata}")
        except Exception as e:
            logger.error(f"Error in metadata handler: {e}")
    
    def on_unhandled(self, self_param, unhandled, **kwargs):
        """Handle unhandled events from Deepgram."""
        logger.debug(f"Unhandled Deepgram event: {unhandled}") 