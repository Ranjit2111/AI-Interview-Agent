"""
API module for the interview preparation system.
Defines REST endpoints for interacting with the application.
"""

import logging
from fastapi import FastAPI

from backend.api.agent_api import create_agent_api
from backend.api.speech_api import create_speech_api

# Create logger
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    logger.info("Creating API application...")
    
    app = FastAPI(
        title="AI Interview Preparation System",
        description="API for an AI-powered interview preparation system",
        version="0.1.0"
    )
    
    # Add API routes
    logger.info("Registering API routes...")
    create_agent_api(app)
    create_speech_api(app)
    
    # Add health check endpoint
    @app.get("/api/health")
    def health_check():
        """Check API health."""
        return {"status": "ok"}
    
    logger.info("API application created successfully")
    return app 