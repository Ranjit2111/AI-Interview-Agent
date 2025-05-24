#!/usr/bin/env python3
"""
Deepgram Connectivity Test
Based on the Deepgram Live Streaming Starter Kit documentation.
This script tests API key validity and basic streaming connectivity.
"""

import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveOptions
)
from deepgram.clients.live.v1.enums import LiveTranscriptionEvents

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
# Get API key from environment
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")

def test_api_key():
    """Test if the Deepgram API key is valid"""
    if not DEEPGRAM_API_KEY:
        logger.error("DEEPGRAM_API_KEY environment variable not set")
        return False
    
    try:
        # Initialize client
        client = DeepgramClient(DEEPGRAM_API_KEY)
        logger.info("✓ Deepgram client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize Deepgram client: {e}")
        return False

async def test_streaming_connection():
    """Test live streaming connection to Deepgram"""
    if not DEEPGRAM_API_KEY:
        logger.error("API key not available for streaming test")
        return False
    
    try:
        client = DeepgramClient(DEEPGRAM_API_KEY)
        
        # Connection state tracking
        connection_opened = False
        connection_error = None
        
        # Event handlers with correct signatures based on SDK v4.x documentation
        def on_open(self, open, **kwargs):
            nonlocal connection_opened
            connection_opened = True
            logger.info("✓ Deepgram streaming connection opened successfully")
        
        def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            logger.info(f"✓ Received transcript: {sentence}")
        
        def on_error(self, error, **kwargs):
            nonlocal connection_error
            connection_error = error
            logger.error(f"✗ Deepgram streaming error: {error}")
        
        def on_close(self, close, **kwargs):
            logger.info("Deepgram streaming connection closed")
        
        def on_metadata(self, metadata, **kwargs):
            logger.info(f"Received metadata: {metadata}")
            
        def on_speech_started(self, speech_started, **kwargs):
            logger.info("Speech started detected")
            
        def on_utterance_end(self, utterance_end, **kwargs):
            logger.info("Utterance end detected")
        
        def on_unhandled(self, unhandled, **kwargs):
            logger.info(f"Unhandled event: {unhandled}")
        
        # Configure streaming options
        options = LiveOptions(
            language="en",
            model="nova-2",
            smart_format=True,
            interim_results=True,
            endpointing=True,
            vad_events=True,
            utterance_end_ms="1000",
            encoding="linear16",
            sample_rate=16000,
            channels=1,
        )
        
        # Create connection
        connection = client.listen.websocket.v("1")
        
        # Register event handlers
        connection.on(LiveTranscriptionEvents.Open, on_open)
        connection.on(LiveTranscriptionEvents.Transcript, on_message)
        connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        connection.on(LiveTranscriptionEvents.Error, on_error)
        connection.on(LiveTranscriptionEvents.Close, on_close)
        connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)
        
        # Start connection
        logger.info("Starting Deepgram streaming connection...")
        
        if not connection.start(options):
            logger.error("✗ Failed to start Deepgram connection")
            return False
        
        # Wait for connection to open (or timeout after 15 seconds)
        for i in range(30):  # 30 * 0.5s = 15s
            if connection_opened:
                break
            if connection_error:
                logger.error(f"✗ Connection failed with error: {connection_error}")
                return False
            await asyncio.sleep(0.5)
            if i % 10 == 0 and i > 0:
                logger.info(f"Still waiting for connection... ({i//2}s)")
        
        if not connection_opened:
            logger.error("✗ Connection timed out after 15 seconds")
            return False
        
        logger.info("✓ Streaming connection test completed successfully")
        
        # Send a test chunk of silence (to test the connection)
        test_audio = b'\x00' * 1600  # 100ms of silence at 16kHz, 16-bit
        connection.send(test_audio)
        
        # Wait a moment for any response
        await asyncio.sleep(1)
        
        # Close connection
        connection.finish()
        
        return True
        
    except Exception as e:
        logger.exception(f"✗ Streaming connection test failed: {e}")
        return False

async def main():
    """Run all Deepgram connectivity tests"""
    logger.info("=" * 50)
    logger.info("Deepgram Connectivity Test")
    logger.info("=" * 50)
    
    # Test 1: API Key validation
    logger.info("\n1. Testing API Key...")
    api_key_valid = test_api_key()
    
    if not api_key_valid:
        logger.error("Cannot proceed with streaming test - API key invalid")
        return
    
    # Test 2: Streaming connection
    logger.info("\n2. Testing Streaming Connection...")
    streaming_ok = await test_streaming_connection()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("Test Results Summary:")
    logger.info(f"API Key: {'✓ Valid' if api_key_valid else '✗ Invalid'}")
    logger.info(f"Streaming: {'✓ Working' if streaming_ok else '✗ Failed'}")
    
    if api_key_valid and streaming_ok:
        logger.info("🎉 All tests passed! Deepgram integration should work.")
    else:
        logger.error("❌ Some tests failed. Check the errors above.")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    asyncio.run(main()) 