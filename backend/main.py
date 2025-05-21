"""
Main application entry point for the AI Interviewer Agent.
Initializes the FastAPI application and routes.
"""

import os
import logging
import tempfile
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Pydantic imports
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Local imports
from backend.services import initialize_services, get_agent_session_manager
from backend.api.agent_api import create_agent_api
from backend.api.speech_api import create_speech_api
from backend.api.file_processing_api import create_file_processing_api


load_dotenv()
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

root_logger = logging.getLogger()
root_logger.setLevel(log_level)

if root_logger.hasHandlers():
    root_logger.handlers.clear()

formatter = logging.Formatter(log_format)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)
logger.info(f"Logging configured with level: {log_level_str}")

app = FastAPI(
    title="AI Interviewer Agent",
    description="AI-powered interview practice and coaching system",
    version="0.1.0",
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception during request processing for {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"An internal server error occurred: {exc}"}, # Include exc details for debugging
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_agent_api(app)
logger.info("API routes registered")

create_speech_api(app)
logger.info("Speech API routes registered")

create_file_processing_api(app)
logger.info("File Processing API routes registered")

api_key = os.environ.get("GOOGLE_API_KEY", "MISSING_API_KEY")

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "status": "ok",
        "message": "AI Interviewer Agent is running"
    }

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Application startup...")

    try:
        initialize_services() 
        app.state.agent_manager = get_agent_session_manager()
        logger.info("AgentSessionManager attached to app state.")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")

    logger.info("Application startup completed.")

logger.info("Application setup complete. Waiting for Uvicorn server start...")

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True) 