# Setting Up Streaming Speech-to-Text with Deepgram

This guide walks through the setup and usage of the new real-time streaming speech-to-text feature using Deepgram.

## Environment Setup

Add the following environment variables to your `.env` file in the backend directory:

```
# Deepgram for streaming speech-to-text
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

## Getting a Deepgram API Key

1. Create an account at [Deepgram](https://deepgram.com/).
2. Navigate to the API Keys section in your Deepgram Console.
3. Create a new API key with appropriate permissions (Speech recognition).
4. Copy the key and add it to your `.env` file.

## Using the Streaming Speech-to-Text Feature

### In the Frontend

The interface now includes a toggle switch to choose between:

- **Batch Mode**: Records your full answer and then transcribes it (using AssemblyAI).
- **Streaming Mode** (default): Transcribes your speech in real-time as you speak (using Deepgram).

To use streaming mode:

1. Click the "Start Listening" button.
2. Begin speaking - you'll see your words appear on the screen in real-time.
3. When you're done speaking, click "Stop Listening".
4. Your complete transcribed answer will be submitted to the interviewer.

### Speech Detection Feature

The system now includes enhanced speech detection capabilities:

- **Speech Start Detection**: Visual indicator shows when your speech is first detected
- **Real-time Transcription**: See your words appear as you speak
- **Utterance End Detection**: System recognizes when you've finished speaking
- **Visual Feedback**: UI changes show when speech is detected and when each utterance ends

These features create a more natural conversation experience, similar to talking with a real interviewer who can see when you start and stop speaking.

### Benefits of Streaming Mode

- **Real-time feedback**: See your words as you speak them.
- **More natural conversation flow**: Similar to a real interview experience.
- **No waiting**: No delay waiting for transcription after you finish speaking.
- **Corrections on-the-fly**: You can see if the transcription makes mistakes while you're still speaking.
- **Speech detection indicators**: Visual feedback when your voice is detected.
- **Natural pauses**: System detects when you've finished speaking.

## Technical Details

- Streaming mode uses WebSocket connections for real-time audio processing.
- Audio is captured in small chunks (100ms) and sent to the Deepgram API.
- The server uses Deepgram's Nova model with smart formatting for high-quality transcriptions.
- Voice Activity Detection (VAD) events provide speech start and end notifications.
- Both interim and final transcription results are displayed to provide immediate feedback.
- The system waits for 1 second of silence before finalizing an utterance.

## Troubleshooting

- **Microphone access denied**: Ensure your browser has permission to access your microphone.
- **Connection issues**: Check your internet connection stability.
- **Transcription quality issues**: Try speaking clearly and reducing background noise.
- **Speech detection sensitivity**: If speech detection seems too sensitive or not sensitive enough, speak at a consistent volume.

## Fallback Option

If you experience any issues with streaming mode, you can always switch back to batch mode using the toggle.
