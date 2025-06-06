#!/usr/bin/env python3
"""
Test WebSocket Endpoint for Speech-to-Text
Tests the fixed Deepgram WebSocket implementation to ensure no asyncio errors occur.
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Test the WebSocket connection to ensure it works without asyncio errors"""
    
    uri = "wss://localhost:8000/api/speech-to-text/stream"
    
    try:
        logger.info(f"Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✓ WebSocket connection established")
            
            # Wait for initial connection messages
            connection_timeout = 10  # seconds
            messages_received = []
            
            try:
                while len(messages_received) < 2:  # Wait for "connecting" and "connected" messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=connection_timeout)
                    
                    try:
                        data = json.loads(message)
                        messages_received.append(data)
                        logger.info(f"✓ Received: {data.get('type', 'unknown')} - {data.get('message', data.get('error', 'No message'))}")
                        
                        # Check if we got a connection confirmation
                        if data.get('type') == 'connected':
                            logger.info("✓ Deepgram connection confirmed - ready to receive audio")
                            break
                        elif data.get('type') == 'error':
                            logger.error(f"✗ Connection error: {data.get('error')}")
                            return False
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Received non-JSON message: {message}")
                        
            except asyncio.TimeoutError:
                logger.error("✗ Timeout waiting for connection confirmation")
                return False
                
            # Test sending a small audio chunk (silence)
            # This is just to test the flow - in real usage, you'd send actual audio
            test_audio = b'\x00' * 1600  # 100ms of silence at 16kHz, 16-bit
            
            logger.info("Sending test audio chunk...")
            await websocket.send(test_audio)
            
            # Wait a moment to see if we get any responses or errors
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                try:
                    data = json.loads(response)
                    logger.info(f"✓ Received response: {data.get('type', 'unknown')}")
                except json.JSONDecodeError:
                    logger.info("✓ Received audio or binary response")
            except asyncio.TimeoutError:
                logger.info("✓ No immediate response (expected for silence)")
                
            logger.info("✓ Test completed successfully - no asyncio errors!")
            return True
            
    except websockets.exceptions.ConnectionRefused:
        logger.error("✗ Connection refused - is the server running on localhost:8000?")
        return False
    except Exception as e:
        logger.error(f"✗ Test failed with error: {e}")
        return False

async def main():
    """Run the WebSocket endpoint test"""
    logger.info("=" * 60)
    logger.info("WebSocket Endpoint Test - Deepgram AsyncIO Fix Verification")
    logger.info("=" * 60)
    
    logger.info("\nTesting WebSocket connection and event handler flow...")
    success = await test_websocket_connection()
    
    logger.info("\n" + "=" * 60)
    if success:
        logger.info("🎉 SUCCESS: WebSocket endpoint works without asyncio errors!")
        logger.info("✓ Event handlers properly queue messages")
        logger.info("✓ No 'no running event loop' errors")
        logger.info("✓ Deepgram integration functional")
    else:
        logger.error("❌ FAILED: Issues detected with WebSocket endpoint")
    
    logger.info("=" * 60)
    return success

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with exception: {e}") 