# Environment Setup Guide

## Fixing the Deepgram Connection Timeout Issue

The Deepgram connection timeout you're experiencing is caused by a missing `DEEPGRAM_API_KEY` environment variable. Here's how to fix it:

## 1. Create a .env file

Create a `.env` file in the `backend` directory with the following content:

```bash
# Environment Configuration for AI Interviewer Agent

# Deepgram API Configuration (required for streaming speech-to-text)
# Get your API key from: https://console.deepgram.com/
DEEPGRAM_API_KEY=your_actual_deepgram_api_key_here

# AssemblyAI API Configuration (for batch speech-to-text)
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here

# AWS Configuration (for Amazon Polly TTS)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1

# Google API Configuration (for the AI agents)
GOOGLE_API_KEY=your_google_api_key_here

# Application Configuration
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
```

## 2. Get Your Deepgram API Key

1. Go to [https://console.deepgram.com/](https://console.deepgram.com/)
2. Sign up for a free account if you don't have one
3. Navigate to the "API Keys" section
4. Create a new API key
5. Copy the API key and replace `your_actual_deepgram_api_key_here` in your `.env` file

## 3. Update Your Existing Credentials

Since you already have AWS credentials configured, copy them to the `.env` file as well to ensure consistency.

## 4. Test the Configuration

After setting up the `.env` file, you can test the Deepgram connection using:

```bash
cd backend
python test_deepgram.py
```

This will validate your API key and test the streaming connection.

## Troubleshooting

### Common Issues:

1. **"API key not configured"**: Make sure the `.env` file is in the `backend` directory and the API key is correctly set.

2. **"Connection timeout"**: This can be caused by:
   - Invalid API key
   - Network connectivity issues
   - Firewall blocking WebSocket connections
   - Proxy/VPN interference

3. **"Import errors"**: Make sure you've installed the latest Deepgram SDK:
   ```bash
   pip install --upgrade deepgram-sdk
   ```

### Network Connectivity Test:

If you're still experiencing timeouts after setting the API key, try testing network connectivity:

```bash
# Test basic connectivity to Deepgram
curl -X GET "https://api.deepgram.com/v1/projects" \
  -H "Authorization: Token YOUR_API_KEY"
```

## Security Note

Never commit your `.env` file to version control. The `.env` file is already included in `.gitignore` to prevent accidental commits. 