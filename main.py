"""
Main entry point for the interview preparation system backend.
"""

import os
import logging
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import create_app
from backend.database.connection import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/app-{datetime.now().strftime('%Y%m%d')}.log", mode='a', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def setup_cors(app: FastAPI) -> None:
    """
    Setup CORS middleware for the application.
    
    Args:
        app: FastAPI application
    """
    origins = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # Add production origins from environment if available
    if os.environ.get("ALLOWED_ORIGINS"):
        origins.extend(os.environ.get("ALLOWED_ORIGINS").split(","))
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def main():
    """Initialize and run the application."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Create FastAPI app
    logger.info("Creating application...")
    app = create_app()
    
    # Setup CORS
    logger.info("Setting up CORS...")
    setup_cors(app)
    
    # Run with uvicorn
    logger.info("Starting server...")
    uvicorn.run(
        app,
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 8000)),
        log_level="info"
    )


if __name__ == "__main__":
    main() 