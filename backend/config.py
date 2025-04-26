"""
Configuration management for the AI Interviewer Agent.
Provides centralized configuration and logging setup.
"""

import os
import logging
from typing import Optional

# REMOVED basicConfig call from here - should be configured once in main.py
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for the specified module.
    Uses the root logger configuration set in main.py.
    
    Args:
        name: Module name for the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get the logger for the specific module name
    logger = logging.getLogger(name)
    
    # The level and handlers are inherited from the root logger setup in main.py.
    # We don't need to set the level again here unless we want this specific logger
    # to have a different level than the root logger.
    # log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    # logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    return logger 