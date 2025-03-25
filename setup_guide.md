# AI Interviewer Agent - Setup Guide

This guide provides detailed instructions for setting up and running the AI Interviewer Agent project, including both the frontend and backend components.

## Prerequisites

- **Python 3.9+** (Python 3.10.x is recommended)
- **Node.js 14+** and npm
- **Google API Key** for Gemini AI integration

## Step 1: Clone and Set Up Environment Files

1. Clone the repository (if you haven't already):

   ```
   git clone https://github.com/yourusername/ai-interviewer-agent.git
   cd ai-interviewer-agent
   ```
2. Set up environment variables:

   - Copy the `.env.example` file in the backend directory to `.env`:
     ```
     cp backend/.env.example backend/.env
     ```
   - Edit the `.env` file to add your Google API key and other required credentials
   - Create a `.env.local` file in the frontend directory:
     ```
     echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8000" > frontend/.env.local
     ```

## Step 2: Using the Automated Setup Scripts

The project provides two automated setup scripts:

### Option A: Using start_all_services.py (Recommended for most users)

This Python script will set up and start both the frontend and backend services:

```bash
python start_all_services.py
```

The script performs the following actions:

- Verifies required directories and files
- Sets up a Python virtual environment for the backend
- Installs backend dependencies
- Starts the backend FastAPI server
- Installs frontend dependencies
- Starts the Next.js development server

You can also use the following flags:

- `--no-frontend`: Start only the backend
- `--no-backend`: Start only the frontend
- `--tts`: Include Kokoro TTS server (optional speech synthesis)

### Option B: Using start.ps1 (Windows PowerShell)

For Windows users, an alternative PowerShell script is available:

```powershell
./start.ps1
```

This script provides similar functionality to the Python version but is specifically designed for Windows environments. It supports the following parameters:

- `-SkipBackend`: Start only the frontend
- `-SkipFrontend`: Start only the backend
- `-Help`: Display help information

## Step 3: Manual Setup (If Automated Scripts Fail)

If the automated scripts don't work for your environment, you can manually set up the project:

### Backend Setup

1. Create and activate a Python virtual environment:

   ```bash
   cd backend
   python -m venv .venv

   # On Windows
   .\.venv\Scripts\activate

   # On macOS/Linux
   source .venv/bin/activate
   ```
2. Install dependencies:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Start the backend server:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```
2. Install dependencies:

   ```bash
   npm install
   ```
3. Start the development server:

   ```bash
   npm run dev
   ```

## Step 4: Accessing the Application

Once both servers are running:

1. Backend API will be available at: http://localhost:8000
2. Frontend interface will be available at: http://localhost:3000

## Troubleshooting

### Backend Issues

1. **Virtual Environment Problems**

   - Try deleting the `.venv` directory and recreating it
   - Ensure you're using Python 3.9+ (`python --version`)
2. **Dependency Errors**

   - Make sure you have the correct version of Python
   - Try installing dependencies one by one to pinpoint the issue
3. **API Key Issues**

   - Verify your Google API key is correctly set in the `.env` file
   - Ensure the API key has access to the Gemini models

### Frontend Issues

1. **Node Module Errors**

   - Delete the `node_modules` directory and run `npm install` again
   - Verify your Node.js version (`node --version`)
2. **Connection to Backend**

   - Verify the `NEXT_PUBLIC_BACKEND_URL` in `.env.local` is correct
   - Ensure the backend server is running and accessible
3. **Build Errors**

   - Check for syntax errors in the component files
   - Ensure all dependencies are correctly installed

## Creating a Simple Run Script

If you prefer a simpler approach, here's a basic shell script that you can create to start both services:

Create a file named `run.sh` (Linux/macOS) or `run.bat` (Windows) with the following content:

For Linux/macOS (`run.sh`):

```bash
#!/bin/bash

# Start backend
cd backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
cd ..

# Start frontend
cd frontend
npm run dev
```

For Windows (`run.bat`):

```batch
@echo off
start cmd /k "cd backend && .\.venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
start cmd /k "cd frontend && npm run dev"
```

Make the script executable (Linux/macOS):

```bash
chmod +x run.sh
```

## Next Steps

After setting up the application:

1. Complete your profile in the user context form
2. Start an interview session
3. Interact with the interviewer AI
4. Review your feedback and skill assessment

Enjoy using the AI Interviewer Agent for your interview preparation!
