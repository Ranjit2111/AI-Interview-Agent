# AI Interviewer Agent - Setup Guide

This guide provides instructions for running the AI Interviewer Agent with the updated frontend.

## Quick Start

For the fastest way to get started:

1. Run the setup script:
   ```
   run_project.bat
   ```

This script:

- Checks for required dependencies (Python and Node.js)
- Sets up environment files
- Fixes known issues (lodash dependency and backend import)
- Starts both the backend and frontend servers in separate windows

## What the Setup Script Fixes

The script automatically fixes two common issues:

1. **Frontend Dependency**: Installs the required `lodash` package
2. **Backend Module Resolution**: Sets up proper PYTHONPATH to ensure the backend module can be found

## Monitoring the Setup

The script will:

- Show detailed progress of each step
- Display error messages if anything goes wrong
- Not close unexpectedly, allowing you to see any errors
- Create backup files before making changes

## Manual Setup (If Needed)

If you prefer to manually set up the project:

### Backend Setup:

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
   .\.venv\Scripts\activate
   ```
4. Install dependencies:

   ```
   pip install -r requirements.txt
   ```
5. If you encounter module import errors, set the PYTHONPATH environment variable:

   - Windows: `set PYTHONPATH=..`
   - macOS/Linux: `export PYTHONPATH=..`

   This ensures that the `backend` module can be found by Python.
6. Start the backend server:

   ```
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup:

1. Navigate to the frontend directory:

   ```
   cd frontend
   ```
2. Install dependencies:

   ```
   npm install
   ```
3. Install lodash specifically:

   ```
   npm install --save lodash
   ```
4. Start the frontend development server:

   ```
   npm run dev
   ```

## Accessing the Application

Once the servers are running:

- Frontend interface: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)

## Troubleshooting

If you experience issues:

1. **Windows not staying open**: Make sure you're running the latest `run_project.bat` file which includes error handling to prevent windows from closing unexpectedly.
2. **Backend import errors**: If you see `ModuleNotFoundError: No module named 'backend'`, try one of these approaches:

   - Run the backend from the project root directory: `python -m backend.main`
   - Set PYTHONPATH: `set PYTHONPATH=.` (from project root)
   - Set PYTHONPATH: `set PYTHONPATH=..` (from backend directory)
3. **Frontend build errors**: If you see errors related to missing modules, try running a complete install in the frontend directory:

   ```
   cd frontend
   npm install
   npm run dev
   ```

### SQLAlchemy Reserved Attribute Name 'metadata'

If you encounter the following error when starting the backend:
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API
```

This is due to a conflict with SQLAlchemy's reserved keywords. We've fixed this by:

1. Renaming the `metadata` columns in the models:
   - `Question.metadata` → `Question.question_metadata`
   - `ResourceTracking.metadata` → `ResourceTracking.tracking_metadata`
   - `Transcript.metadata` → `Transcript.transcript_metadata`

2. Adding a database migration script (`migrate_db.py`) that handles:
   - Migrating existing databases by renaming columns
   - Resetting the database if needed

#### Using the Database Migration Script

The script is automatically called during project startup, but you can also run it manually:

1. To migrate an existing database:
   ```
   python migrate_db.py --migrate
   ```

2. To reset the database (if migration fails):
   ```
   python migrate_db.py --reset
   ```

> **Note**: Resetting the database will delete all existing data. Use with caution.
