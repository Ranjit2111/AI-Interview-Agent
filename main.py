"""
Main entry point for the AI Interviewer Agent.
Runs the backend FastAPI application.
"""

import os
import logging
from datetime import datetime

import uvicorn

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


def main():
    """Initialize and run the application."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the backend FastAPI application
    logger.info("Starting AI Interviewer Agent...")
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "backend.main:app", 
        host=host, 
        port=port, 
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main() 