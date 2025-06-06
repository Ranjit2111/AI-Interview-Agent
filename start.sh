#!/bin/bash

# Exit on any error
set -e

echo "Starting AI Interviewer Backend..."

# Set environment variables for production
export PYTHONPATH=/app
export HOST=0.0.0.0
export PORT=${PORT:-8000}

# Print environment info for debugging
echo "Python path: $PYTHONPATH"
echo "Host: $HOST"
echo "Port: $PORT"
echo "Working directory: $(pwd)"

# Start the FastAPI application
exec uvicorn main:app --host $HOST --port $PORT --workers 1 --log-level info 