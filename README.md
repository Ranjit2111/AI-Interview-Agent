# AI Interviewer Agent

An AI-powered interview coaching system that helps users prepare for job interviews with adaptive questions and real-time feedback.

## Overview

This application provides a comprehensive interview preparation experience with the following features:

- **Job Context Setup**: Upload your job role, description, and resume for targeted interview preparation
- **Live Interview Simulation**: Practice with AI-generated questions specific to your job context
- **Audio Response Analysis**: Record and analyze your verbal responses
- **Visual Interface**: Use your camera to practice your interview presence
- **Performance Feedback**: Review your performance with AI-powered insights

## Local Setup

This project has been configured to run entirely locally on your computer.

### Prerequisites

- **Python 3.10** - For the backend server (recommended for best compatibility)
- **Node.js 14+** - For the frontend server
- **A Google Gemini API Key** - For AI functionality

### Quick Start

1. Clone this repository
2. Edit `backend/.env` to add your Google Gemini API key
3. Run the startup script:

```
# Windows (PowerShell)
.\start_fixed.ps1
```

This script will automatically:
- Check for Python 3.10 and Node.js
- Set up the Python virtual environment for the backend
- Install all required dependencies
- Start both the frontend and backend servers

### Manual Setup

If you prefer to set up the application manually:

#### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment:
   ```
   python -m venv .venv
   ```

3. Activate the virtual environment:
   ```
   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   
   # Linux/macOS
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Create or edit `.env` file with your API key:
   ```
   API_KEY=your_gemini_api_key_here
   PORT=8000
   HOST=0.0.0.0
   ```

6. Start the backend server:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Create or edit `.env.local` file:
   ```
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```

4. Start the frontend development server:
   ```
   npm run dev
   ```

5. Access the application at `http://localhost:3000`

## Project Structure

```
AI-Interviewer-Agent/
├── backend/
│   ├── .venv/             # Python virtual environment
│   ├── temp/              # Temporary storage for audio files
│   ├── .env               # Environment variables with API keys
│   ├── .env.example       # Example environment file
│   ├── main.py            # FastAPI application
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── components/        # React components
│   ├── pages/             # Next.js pages
│   ├── styles/            # CSS styles
│   ├── .env.local         # Frontend environment variables
│   └── package.json       # JavaScript dependencies
├── start_fixed.ps1        # Unified startup script
├── README.md              # This documentation
└── project_revision.md    # Project revision plan
```

## Usage

1. **Job Setup**: Start by entering your job role and description, and optionally upload your resume.
2. **Interview**: After submitting job details, you'll be taken to the interview section where you can respond to AI-generated questions by text or audio recording.
3. **Feedback**: Review your performance in the feedback section.

## Troubleshooting

### Backend Issues

- **Python Version Mismatch**: This application works best with Python 3.10. If you're using a different version, you may encounter dependency issues.
- **API Key Error**: Ensure your Gemini API key is properly configured in `backend/.env`
- **Port Already in Use**: If port 8000 is already used, modify the port in `backend/.env` and ensure it matches in `frontend/.env.local`
- **Missing Dependencies**: Make sure you've activated the virtual environment and installed requirements

### Frontend Issues

- **Connection Error**: Ensure the backend server is running before starting the frontend
- **Media Access**: The application requires camera access - check your browser permissions
- **Styling Issues**: If styles don't load correctly, try clearing your browser cache

### Common Fixes

- **Reset the Environment**: Delete the `backend/.venv` folder and run the setup script again
- **Update Dependencies**: Run `pip install -r requirements.txt` in the backend folder and `npm install` in the frontend folder
- **Clear Temp Files**: Delete the `backend/temp` folder if you encounter file-related errors

## Development

The application consists of two main components:

1. **Frontend**: A Next.js application with React components
   - Uses TailwindCSS for styling
   - Includes camera and audio recording functionality
   - Communicates with the backend via fetch API

2. **Backend**: A FastAPI server that handles AI processing and file management
   - Uses the Google Gemini Pro API for generating interview questions
   - Handles file uploads (resumes) and audio processing
   - Provides a RESTful API for the frontend

Key files:
- `frontend/pages/index.js`: The main application UI
- `frontend/components/CameraView.js`: Camera handling component
- `backend/main.py`: The FastAPI server endpoints and business logic

## License

This project is for educational purposes only.

## Acknowledgments

- Powered by Google's Gemini Pro model for AI functionality
- Built with Next.js, FastAPI, and TailwindCSS 