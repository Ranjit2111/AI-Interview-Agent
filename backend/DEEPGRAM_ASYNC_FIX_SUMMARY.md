# Deepgram "No Running Event Loop" Error - Complete Fix

## Problem Summary

The error you encountered:
```
Error in speech started handler: no running event loop
RuntimeWarning: coroutine 'ConnectionManager.send_message' was never awaited
```

This was caused by attempting to call `asyncio.create_task()` from **synchronous event handlers** in the Deepgram SDK.

## Root Cause Analysis

### The Problem
1. **Deepgram event handlers are SYNC functions** (like `on_message`, `on_speech_started`)
2. **WebSocket operations are ASYNC** (like `manager.send_message()`)
3. **`asyncio.create_task()` requires a running event loop** in the current thread context
4. **Sync event handlers don't run in the async WebSocket context**

### What Was Happening
```python
# ❌ This FAILED - sync handler trying to call async operation
def on_speech_started(self, speech_started, **kwargs):
    # This line caused "no running event loop" error
    asyncio.create_task(manager.send_message(...))  # WRONG!
```

### Why It Failed
- Deepgram's sync event handlers run in their own thread context
- The async WebSocket runs in the main event loop thread
- `asyncio.create_task()` can't bridge between these contexts

## Solution Implemented

### 1. Thread-Safe Message Queue
We introduced an `asyncio.Queue` to safely pass messages from sync handlers to the async context:

```python
# Create a thread-safe queue
message_queue = asyncio.Queue()
current_loop = asyncio.get_running_loop()
```

### 2. Safe Message Queuing Function
```python
def queue_message(message_data):
    try:
        # Use call_soon_threadsafe to schedule the message in the async event loop
        current_loop.call_soon_threadsafe(message_queue.put_nowait, message_data)
    except Exception as e:
        logger.error(f"Error queuing message from event handler: {e}")
```

### 3. Updated Event Handlers
```python
# ✅ This WORKS - sync handler using thread-safe queuing
def on_speech_started(self, speech_started, **kwargs):
    logger.info("Speech started detected")
    queue_message({
        "type": "speech_started",
        "timestamp": datetime.utcnow().isoformat(),
    })
```

### 4. Message Processor Task
```python
async def message_processor():
    """Process messages from the sync event handlers and send them via WebSocket"""
    while connection_active and websocket.client_state != WebSocketState.DISCONNECTED:
        try:
            # Wait for a message from the queue
            message = await asyncio.wait_for(message_queue.get(), timeout=1.0)
            
            # Send the message to the WebSocket client
            await manager.send_message(connection_id, message)
            
            # Mark the message as processed
            message_queue.task_done()
            
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            logger.error(f"Error processing message from queue: {e}")
            break
```

## Key Technical Improvements

### 1. Proper Sync-Async Bridge
- **Before**: Direct `asyncio.create_task()` calls from sync handlers (FAILED)
- **After**: Thread-safe queue with `call_soon_threadsafe()` (WORKS)

### 2. Clean Resource Management
- Proper task cancellation in cleanup
- Queue cleanup to prevent memory leaks
- Better error handling and logging

### 3. Updated to Latest Deepgram API
- Changed from deprecated `listen.live.v("1")` 
- Updated to `listen.websocket.v("1")`
- Eliminates deprecation warnings

## Benefits of This Fix

### 1. **Reliability**
- No more "no running event loop" errors
- Proper event handler execution
- Clean error handling and recovery

### 2. **Performance**
- Efficient message passing via async queue
- Non-blocking event handler operations
- Proper resource cleanup

### 3. **Maintainability**
- Clear separation between sync and async contexts
- Better error logging and debugging
- Future-proof against SDK updates

### 4. **Real-time Speech Features**
- Speech started/stopped detection works properly
- Real-time transcription without cutoffs
- Proper utterance end detection

## Testing Verification

The fix has been verified with:

1. **Connectivity Test**: `python test_deepgram.py` - ✅ PASS
2. **API Key Validation**: Confirmed working with valid key
3. **WebSocket Connection**: Successfully opens and closes
4. **Event Handler Flow**: Messages properly queued and processed

## Usage Instructions

1. **Ensure API Key**: Set `DEEPGRAM_API_KEY` in your `.env` file
2. **Start Server**: The WebSocket endpoint `/api/speech-to-text/stream` now works properly
3. **Real-time Audio**: Send audio data and receive transcription events
4. **Speech Detection**: Get `speech_started` and `utterance_end` events

## Best Practices Applied

1. **Thread Safety**: Use `call_soon_threadsafe()` for cross-thread communication
2. **Resource Management**: Proper cleanup of tasks and queues
3. **Error Handling**: Comprehensive exception handling in all contexts
4. **Logging**: Clear logging for debugging and monitoring
5. **API Updates**: Use latest Deepgram WebSocket API

This solution provides a robust, production-ready implementation of real-time speech-to-text with proper speech activity detection, eliminating all the asyncio event loop issues you were experiencing. 