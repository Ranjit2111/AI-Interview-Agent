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

# Removed redundant create_app function and /api/health route.
# App creation and routing are handled in main.py. 