# Speech Functionality

This document describes the speech functionality implemented in Sprint 4 of the AI Interviewer Agent.

## Overview

The AI Interviewer Agent now supports speech input and output, providing a more natural and immersive interview experience. Users can speak their answers and listen to the interviewer's questions, making the interaction more realistic.

## Features

### Speech-to-Text

- **Web Speech API Integration**: Uses the browser's native Web Speech API for real-time speech recognition
- **Fallback to AssemblyAI**: For browsers without Web Speech API support, falls back to AssemblyAI for server-side transcription
- **Error Handling**: Provides clear feedback when speech recognition is not available or encounters errors
- **Real-time Transcription**: Shows transcription as users speak, with options to toggle visibility

### Text-to-Speech

- **Kokoro TTS Integration**: Uses Kokoro TTS for high-quality, natural-sounding speech synthesis
- **Voice Selection**: Allows users to choose from multiple voices with different characteristics
- **Streaming Audio**: Supports streaming of audio with word-level timestamps
- **Audio Controls**: Provides play/pause controls and visual feedback during speech playback

## Setup Instructions

### Speech-to-Text Setup

1. **Web Speech API**: No setup required for browser-based recognition
2. **AssemblyAI Integration (Optional)**:
   - Sign up for an API key at [AssemblyAI](https://www.assemblyai.com/)
   - Add your API key to the `.env` file: `ASSEMBLYAI_API_KEY=your_key_here`

### Text-to-Speech Setup

1. **Install Kokoro TTS**:
   ```bash
   python backend/setup_kokoro_tts.py
   ```
   This script will:
   - Clone the Kokoro TTS repository
   - Set up a virtual environment
   - Install dependencies
   - Create a startup script

2. **Start the Kokoro TTS Server**:
   - On Windows: Run the `start_kokoro.bat` script
   - On Unix/Linux: Run the `start_kokoro.sh` script

3. **Configure the AI Interviewer Agent**:
   - Ensure the `KOKORO_API_URL` in your `.env` file points to your Kokoro TTS server (default: `http://localhost:8008`)

## Usage

### Using Speech Input

1. Navigate to the Interview section
2. Check the "Voice Input" checkbox to enable speech recognition
3. Click the microphone button to start speaking
4. Your transcribed speech will appear and be automatically submitted when you pause

### Using Speech Output

1. Navigate to the Interview section
2. Check the "Voice Output" checkbox to enable text-to-speech
3. After receiving a response from the interviewer, the text-to-speech controls will appear
4. Select a voice from the dropdown menu
5. Click the speaker button to listen to the response

## Implementation Details

### Speech-to-Text Architecture

- Frontend components:
  - `SpeechRecognition.js`: Core hook for Web Speech API integration
  - `SpeechInput.js`: User interface component for speech input

- Backend components:
  - `speech_api.py`: API endpoints for AssemblyAI integration (fallback)

### Text-to-Speech Architecture

- Frontend components:
  - `SpeechOutput.js`: User interface component for voice selection and playback

- Backend components:
  - `speech_api.py`: API endpoints for Kokoro TTS integration

## Troubleshooting

### Speech-to-Text Issues

- **"Speech recognition is not supported in this browser"**: Your browser doesn't support the Web Speech API. Try using Chrome or Edge, or use the fallback audio file upload option.
- **AssemblyAI errors**: Check your API key and internet connection. The server logs will provide more details.

### Text-to-Speech Issues

- **"Text-to-speech service is not available"**: Make sure the Kokoro TTS server is running and the `KOKORO_API_URL` is correctly set in your `.env` file.
- **No audio playing**: Check your audio output settings and ensure your browser has permission to play audio.

## Further Development

Future enhancements for speech functionality may include:

- Emotion detection in speech input
- More voice options and languages
- Synchronization of speech with on-screen text highlighting
- Voice customization options (pitch, speed, etc.)
- Support for additional TTS providers 