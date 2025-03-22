"""
API module for the interview preparation system.
Defines REST endpoints for interacting with the application.
"""

from fastapi import FastAPI

from backend.api.agent_api import create_agent_api

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="AI Interview Preparation System",
        description="API for an AI-powered interview preparation system",
        version="0.1.0"
    )
    
    # Add API routes
    create_agent_api(app)
    
    # Add health check endpoint
    @app.get("/api/health")
    def health_check():
        """Check API health."""
        return {"status": "ok"}
    
    return app 