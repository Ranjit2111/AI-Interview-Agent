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
from backend.services import initialize_services, get_session_registry, get_rate_limiter
from backend.api.agent_api import create_agent_api
from backend.api.speech_api import create_speech_api
from backend.api.file_processing_api import create_file_processing_api
from backend.api.auth_api import create_auth_api
from backend.middleware import SessionSavingMiddleware


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

# Add session saving middleware for automatic session persistence
app.add_middleware(SessionSavingMiddleware)

# Register API routes
create_auth_api(app)
logger.info("Auth API routes registered")

create_agent_api(app)
logger.info("Agent API routes registered")

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

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    try:
        session_registry = get_session_registry()
        active_sessions = await session_registry.get_active_session_count()
        memory_stats = await session_registry.get_memory_usage_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "active_sessions": active_sessions,
            "memory_stats": memory_stats,
            "services": {
                "database": "connected",
                "llm_service": "available",
                "event_bus": "running"
            }
        }
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.get("/metrics")
async def get_metrics():
    """Get system metrics for monitoring."""
    try:
        session_registry = get_session_registry()
        rate_limiter = get_rate_limiter()
        
        active_sessions = await session_registry.get_active_session_count()
        memory_stats = await session_registry.get_memory_usage_stats()
        rate_limit_stats = rate_limiter.get_usage_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "sessions": {
                "active": active_sessions,
                **memory_stats
            },
            "rate_limits": rate_limit_stats,
            "system": {
                "version": "0.1.0",
                "status": "running"
            }
        }
    except Exception as e:
        logger.exception(f"Metrics collection failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Metrics collection failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Application startup...")

    try:
        await initialize_services()  # Now async to start cleanup task
        session_registry = get_session_registry()
        app.state.agent_manager = session_registry
        
        # Add verification logging
        logger.info(f"SessionRegistry type: {type(session_registry)}")
        logger.info(f"SessionRegistry has db_manager: {hasattr(session_registry, 'db_manager')}")
        logger.info(f"SessionRegistry has llm_service: {hasattr(session_registry, 'llm_service')}")
        logger.info(f"SessionRegistry has event_bus: {hasattr(session_registry, 'event_bus')}")
        
        if hasattr(session_registry, 'db_manager'):
            logger.info(f"DB Manager type: {type(session_registry.db_manager)}")
        if hasattr(session_registry, 'llm_service'):
            logger.info(f"LLM Service type: {type(session_registry.llm_service)}")
        if hasattr(session_registry, 'event_bus'):
            logger.info(f"Event Bus type: {type(session_registry.event_bus)}")
            
        logger.info("SessionRegistry attached to app state with all dependencies verified.")
        logger.info("Session cleanup task is running in the background.")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        logger.exception("Full startup error details:")
        raise

    logger.info("Application startup completed.")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Application shutdown...")
    
    try:
        # Stop cleanup task and save all active sessions
        session_registry = get_session_registry()
        await session_registry.stop_cleanup_task()
        
        # Final cleanup of all active sessions
        cleaned_count = await session_registry.cleanup_inactive_sessions(max_idle_minutes=0)
        logger.info(f"Shutdown: saved {cleaned_count} active sessions")
        
    except Exception as e:
        logger.exception(f"Error during shutdown: {e}")
    
    logger.info("Application shutdown completed.")

logger.info("Application setup complete. Waiting for Uvicorn server start...")

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True) 