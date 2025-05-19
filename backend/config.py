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
    logger = logging.getLogger(name)
    
    return logger 