"""
Tests for speech API helper classes.
Tests the helper classes extracted from speech_api.py for better organization.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, MagicMock
from backend.api.speech_api import (
    DeepgramEventHandlers, WebSocketMessageProcessor, 
    _create_deepgram_options, _prepare_tts_ssml
)


class TestDeepgramEventHandlers:
    """Test the DeepgramEventHandlers helper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.message_queue = asyncio.Queue()
        self.current_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.current_loop)
        self.handlers = DeepgramEventHandlers(self.message_queue, self.current_loop)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.current_loop.close()
    
    def test_handlers_initialization(self):
        """Test DeepgramEventHandlers initialization."""
        assert self.handlers.message_queue == self.message_queue
        assert self.handlers.current_loop == self.current_loop
        assert self.handlers.connection_active is False
    
    def test_on_open_handler(self):
        """Test on_open event handler."""
        mock_self = Mock()
        mock_event = Mock()
        
        self.handlers.on_open(mock_self, mock_event)
        
        assert self.handlers.connection_active is True
        # Check if message was queued
        assert not self.message_queue.empty()
    
    def test_on_message_handler_with_transcript(self):
        """Test on_message handler with valid transcript."""
        mock_self = Mock()
        mock_result = Mock()
        mock_result.channel.alternatives = [Mock()]
        mock_result.channel.alternatives[0].transcript = "Hello world"
        mock_result.is_final = True
        
        self.handlers.on_message(mock_self, mock_result)
        
        # Should queue a transcript message
        assert not self.message_queue.empty()
    
    def test_on_message_handler_with_none_transcript(self):
        """Test on_message handler with None transcript."""
        mock_self = Mock()
        mock_result = Mock()
        mock_result.channel.alternatives = [Mock()]
        mock_result.channel.alternatives[0].transcript = None
        mock_result.is_final = False
        
        self.handlers.on_message(mock_self, mock_result)
        
        # Should still queue a message for None transcript
        assert not self.message_queue.empty()
    
    def test_on_speech_started_handler(self):
        """Test on_speech_started event handler."""
        mock_self = Mock()
        mock_event = Mock()
        
        self.handlers.on_speech_started(mock_self, mock_event)
        
        # Should queue speech_started message
        assert not self.message_queue.empty()
    
    def test_on_utterance_end_handler(self):
        """Test on_utterance_end event handler."""
        mock_self = Mock()
        mock_event = Mock()
        
        self.handlers.on_utterance_end(mock_self, mock_event)
        
        # Should queue utterance_end message
        assert not self.message_queue.empty()
    
    def test_on_error_handler(self):
        """Test on_error event handler."""
        mock_self = Mock()
        mock_error = Exception("Test error")
        
        self.handlers.on_error(mock_self, mock_error)
        
        assert self.handlers.connection_active is False
        # Should queue error message
        assert not self.message_queue.empty()
    
    def test_on_close_handler(self):
        """Test on_close event handler."""
        mock_self = Mock()
        mock_event = Mock()
        
        self.handlers.on_close(mock_self, mock_event)
        
        assert self.handlers.connection_active is False
        # Should queue disconnected message
        assert not self.message_queue.empty()
    
    def test_on_metadata_handler(self):
        """Test on_metadata event handler."""
        mock_self = Mock()
        mock_metadata = {"test": "metadata"}
        
        self.handlers.on_metadata(mock_self, mock_metadata)
        
        # Should queue metadata message
        assert not self.message_queue.empty()
    
    def test_on_unhandled_handler(self):
        """Test on_unhandled event handler."""
        mock_self = Mock()
        mock_unhandled = {"unhandled": "event"}
        
        self.handlers.on_unhandled(mock_self, mock_unhandled)
        
        # Should handle gracefully (no exception)
        # This handler just logs, so we verify it doesn't crash
    
    def test_queue_message_error_handling(self):
        """Test error handling in _queue_message method."""
        # Create a closed loop to simulate error
        closed_loop = asyncio.new_event_loop()
        closed_loop.close()
        
        handlers = DeepgramEventHandlers(self.message_queue, closed_loop)
        
        # Should handle the error gracefully
        handlers._queue_message({"test": "message"})
        # No exception should be raised


class TestWebSocketMessageProcessor:
    """Test the WebSocketMessageProcessor helper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.connection_id = "test-connection-123"
        self.manager = Mock()
        self.websocket = Mock()
        self.message_queue = asyncio.Queue()
        
        self.processor = WebSocketMessageProcessor(
            self.connection_id, self.manager, self.websocket, self.message_queue
        )
    
    def test_processor_initialization(self):
        """Test WebSocketMessageProcessor initialization."""
        assert self.processor.connection_id == self.connection_id
        assert self.processor.manager == self.manager
        assert self.processor.websocket == self.websocket
        assert self.processor.message_queue == self.message_queue
    
    @pytest.mark.asyncio
    async def test_process_messages_with_active_connection(self):
        """Test message processing with active connection."""
        # Set up mocks
        handlers = Mock()
        handlers.connection_active = True
        self.websocket.client_state = "CONNECTED"  # Not disconnected
        
        # Put a test message in the queue
        test_message = {"type": "test", "data": "message"}
        await self.message_queue.put(test_message)
        
        # Mock the manager send_message
        self.manager.send_message = AsyncMock()
        
        # Set up to stop the loop after processing one message
        async def side_effect(*args):
            handlers.connection_active = False
        
        self.manager.send_message.side_effect = side_effect
        
        # Process messages
        await self.processor.process_messages(handlers)
        
        # Verify message was sent
        self.manager.send_message.assert_called_once_with(self.connection_id, test_message)
    
    @pytest.mark.asyncio
    async def test_handle_audio_streaming_with_data(self):
        """Test audio streaming handling with incoming data."""
        # Set up mocks
        handlers = Mock()
        handlers.connection_active = True
        deepgram_connection = Mock()
        
        # Mock websocket to return audio data once then stop
        audio_data = b"audio chunk data"
        
        async def mock_receive_bytes():
            handlers.connection_active = False  # Stop after one iteration
            return audio_data
        
        self.websocket.receive_bytes = mock_receive_bytes
        self.websocket.client_state = "CONNECTED"
        
        # Process audio streaming
        await self.processor.handle_audio_streaming(deepgram_connection, handlers)
        
        # Verify audio was sent to Deepgram
        deepgram_connection.send.assert_called_once_with(audio_data)
    
    @pytest.mark.asyncio
    async def test_handle_audio_streaming_timeout(self):
        """Test audio streaming handling with timeout."""
        # Set up mocks
        handlers = Mock()
        handlers.connection_active = True
        deepgram_connection = Mock()
        
        # Mock websocket to timeout
        async def mock_receive_bytes():
            await asyncio.sleep(10)  # Longer than timeout
            return b"data"
        
        self.websocket.receive_bytes = mock_receive_bytes
        self.websocket.client_state = "CONNECTED"
        
        # Set up to stop after first timeout
        timeout_count = 0
        original_active = handlers.connection_active
        
        def mock_active():
            nonlocal timeout_count
            timeout_count += 1
            if timeout_count > 1:
                return False
            return original_active
        
        type(handlers).connection_active = property(lambda self: mock_active())
        
        # Process audio streaming (should handle timeout gracefully)
        await self.processor.handle_audio_streaming(deepgram_connection, handlers)
        
        # Should handle timeout without crashing


class TestUtilityFunctions:
    """Test utility functions extracted from speech_api.py."""
    
    def test_create_deepgram_options(self):
        """Test _create_deepgram_options function."""
        options = _create_deepgram_options()
        
        # Verify options are properly configured
        assert hasattr(options, 'language')
        # We can't easily test all attributes without Deepgram SDK internals
        # but we can verify the function runs without error
    
    def test_prepare_tts_ssml_basic(self):
        """Test _prepare_tts_ssml with basic text."""
        text = "Hello world"
        speed = 1.0
        
        ssml = _prepare_tts_ssml(text, speed)
        
        assert '<speak>' in ssml
        assert '</speak>' in ssml
        assert 'Hello world' in ssml
        assert 'rate="100%"' in ssml
        assert '<break time="250ms"/>' in ssml
    
    def test_prepare_tts_ssml_with_special_chars(self):
        """Test _prepare_tts_ssml with special characters."""
        text = "Hello <world> & friends"
        speed = 1.5
        
        ssml = _prepare_tts_ssml(text, speed)
        
        # Should escape special characters
        assert '&lt;world&gt;' in ssml
        assert '&amp; friends' in ssml
        assert 'rate="150%"' in ssml
    
    def test_prepare_tts_ssml_different_speeds(self):
        """Test _prepare_tts_ssml with different speed values."""
        test_cases = [
            (0.5, "50%"),
            (1.0, "100%"),
            (1.5, "150%"),
            (2.0, "200%")
        ]
        
        for speed, expected_rate in test_cases:
            ssml = _prepare_tts_ssml("test", speed)
            assert f'rate="{expected_rate}"' in ssml
    
    def test_prepare_tts_ssml_structure(self):
        """Test _prepare_tts_ssml output structure."""
        ssml = _prepare_tts_ssml("test text", 1.0)
        
        # Should have proper SSML structure
        assert ssml.startswith('<speak>')
        assert ssml.endswith('</speak>')
        assert '<break time="250ms"/>' in ssml
        assert '<prosody rate=' in ssml
        assert '</prosody>' in ssml 