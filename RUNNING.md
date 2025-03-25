# Running the Updated AI Interviewer Agent

This guide explains how to run the project with the recently updated frontend components.

## Quick Start

The simplest way to run the project is to use the provided batch file:

1. Double-click `run.bat` in the root directory

This will:

- Set up any missing configuration files
- Create a Python virtual environment if needed
- Install backend dependencies
- Install frontend dependencies
- Start both servers in separate windows

## Manual Setup and Running

If you prefer to manually control the setup process, follow these steps:

### 1. Set Up Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Set Up Frontend

In a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Accessing the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Updated Frontend Features

The frontend has been updated with the following enhancements:

1. **Improved Layout Structure**: Organized with clear sections for context, interview, feedback, skills, and transcripts
2. **Enhanced Camera Controls**: Added toggle for enabling/disabling the camera
3. **Better Speech Input**: Enhanced with mute/unmute controls
4. **Chat Window**: New component for displaying the conversation history
5. **Coach Feedback**: Dedicated section for displaying feedback with highlighted conversation parts
6. **Skill Assessment**: Visual representation of skills with detailed information
7. **Dark Mode Support**: Added toggle for light/dark themes
8. **Responsive Design**: Better layout on various screen sizes

## API Integration

The updated frontend integrates with these backend API endpoints:

- `/api/sessions/start`: For starting a new interview session
- `/api/sessions/{sessionId}/message`: For sending messages to the interviewer
- `/api/sessions/{sessionId}/end`: For ending the current session

## Troubleshooting

If you encounter issues:

1. **Backend Connection Problems**:

   - Check that the backend is running on port 8000
   - Verify your `.env` file has the correct API keys
2. **Frontend Issues**:

   - Ensure Node.js 14+ is installed
   - Try deleting `node_modules` and running `npm install` again
   - Check browser console for any errors

## Additional Resources

For more detailed setup instructions and developer documentation, see:

- `setup_guide.md`: Comprehensive setup guide
- `sample_env.txt`: Sample environment variables
- `codebase_guide.md`: Documentation of the codebase
- `component_relationships.md`: How components interact
