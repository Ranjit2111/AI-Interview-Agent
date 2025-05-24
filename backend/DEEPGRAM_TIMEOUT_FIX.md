# Deepgram Connection Timeout Fix

## Issue Summary

The error you encountered:
```
WebSocketException in AbstractSyncWebSocketClient.start: timed out
ListenWebSocketClient.start failed
Deepgram connection failed to open within timeout period
```

This was caused by multiple issues that have now been resolved.

## Root Causes Identified

1. **Missing API Key**: The `DEEPGRAM_API_KEY` environment variable was not configured
2. **SDK Version Mismatch**: Code was written for SDK v4.x but requirements had v2.x
3. **Incorrect Event Handlers**: Event handler signatures were incorrect for the current SDK version
4. **Lack of Connectivity Validation**: No pre-flight checks to validate API key and connectivity

## Solutions Implemented

### 1. Environment Configuration Fix

**Problem**: No `.env` file with the required `DEEPGRAM_API_KEY`

**Solution**: 
- Created environment setup guide in `ENVIRONMENT_SETUP.md`
- You need to create a `.env` file in the `backend` directory with your Deepgram API key

**Required `.env` file content**:
```bash
# Get your API key from: https://console.deepgram.com/
DEEPGRAM_API_KEY=your_actual_deepgram_api_key_here

# Your existing AWS credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

# Other API keys
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### 2. SDK Version Fix

**Problem**: `requirements.txt` had `deepgram-sdk>=2.14.0` but code was using v4.x patterns

**Solution**: Updated to `deepgram-sdk>=4.1.0`

### 3. Event Handler Fixes

**Problem**: Event handlers used incorrect signatures

**Solution**: Updated all event handlers to use the correct v4.x signatures:
```python
def on_open(self, open, **kwargs):
def on_message(self, result, **kwargs):
def on_error(self, error, **kwargs):
# etc.
```

### 4. Improved Connection Options

**Problem**: Missing connection parameters

**Solution**: Added explicit connection options:
```python
options = LiveOptions(
    language="en",
    model="nova-2",
    smart_format=True,
    interim_results=True,
    endpointing=True,
    vad_events=True,
    utterance_end_ms="1000",
    encoding="linear16",  # Explicitly set
    sample_rate=16000,    # Standard sample rate
    channels=1,           # Mono audio
)
```

### 5. Added Diagnostic Tools

**Solution**: Created `test_deepgram.py` to validate connectivity before running the main application

## How to Fix Your Setup

### Step 1: Get Deepgram API Key
1. Go to [https://console.deepgram.com/](https://console.deepgram.com/)
2. Sign up for a free account (includes $200 credit)
3. Navigate to "API Keys" section
4. Create a new API key
5. Copy the API key

### Step 2: Create .env File
Create `backend/.env` with your API key:
```bash
DEEPGRAM_API_KEY=your_actual_api_key_here
# ... other credentials ...
```

### Step 3: Test the Connection
```bash
cd backend
python test_deepgram.py
```

You should see:
```
==================================================
Deepgram Connectivity Test
==================================================

1. Testing API Key...
✓ Deepgram client initialized successfully

2. Testing Streaming Connection...
Starting Deepgram streaming connection...
✓ Deepgram streaming connection opened successfully
✓ Streaming connection test completed successfully

==================================================
Test Results Summary:
API Key: ✓ Valid
Streaming: ✓ Working
🎉 All tests passed! Deepgram integration should work.
==================================================
```

### Step 4: Start Your Application
```bash
cd backend
python main.py
```

## Troubleshooting

### If you still get timeouts:

1. **Check network connectivity**:
   ```bash
   curl -X GET "https://api.deepgram.com/v1/projects" -H "Authorization: Token YOUR_API_KEY"
   ```

2. **Check firewall/proxy**: Ensure WebSocket connections are allowed

3. **Try different network**: Sometimes VPNs or corporate networks block WebSocket connections

4. **Verify API key permissions**: Ensure your API key has streaming permissions

### Common Error Messages:

- `"API key not configured"` → Missing or invalid `.env` file
- `"Connection timeout"` → Network issues or invalid API key  
- `"Import errors"` → Wrong SDK version installed

## Benefits of This Fix

1. **Real-time Speech Detection**: Now properly detects when speech starts/stops
2. **Better Error Handling**: Clear error messages and recovery
3. **Improved Reliability**: Proper connection management and keep-alive
4. **Diagnostic Tools**: Easy testing and validation
5. **Future-Proof**: Uses latest SDK patterns and best practices

## Implementation Details

The fix involved updating the WebSocket endpoint in `backend/api/speech_api.py` with:

- Proper API key validation
- Correct event handler signatures  
- Better connection state management
- Enhanced error reporting
- Async/sync compatibility fixes

The streaming STT service now provides the natural interview experience you were aiming for, with real-time speech detection similar to talking with a real interviewer. 