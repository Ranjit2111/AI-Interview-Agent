"""
Configuration management for the AI Interviewer Agent.
Provides centralized configuration and logging setup.
"""

import os
import logging
from typing import Optional, Dict, Any


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


def create_session_logger(name: str, session_id: Optional[str] = None, 
                         user_id: Optional[str] = None) -> logging.Logger:
    """
    Create a logger with session context for enhanced Azure debugging.
    
    Args:
        name: Module name for the logger
        session_id: Optional session ID to include in logs
        user_id: Optional user ID to include in logs
        
    Returns:
        logging.Logger: Enhanced logger with session context
    """
    logger = logging.getLogger(name)
    
    # Create a custom LoggerAdapter to automatically add session context
    class SessionLoggerAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            # Add session context to extra fields
            extra = kwargs.get('extra', {})
            if session_id:
                extra['session_id'] = session_id
            if user_id:
                extra['user_id'] = user_id
            kwargs['extra'] = extra
            return msg, kwargs
    
    return SessionLoggerAdapter(logger, {})


def get_environment_info() -> Dict[str, Any]:
    """
    Get current environment information for debugging.
    
    Returns:
        Dict containing environment details
    """
    return {
        "is_azure": os.environ.get("WEBSITES_PORT") is not None,
        "python_path": os.environ.get("PYTHONPATH"),
        "log_level": os.environ.get("LOG_LEVEL", "INFO"),
        "has_aws_region": bool(os.environ.get("AWS_REGION")),
        "has_openai_key": bool(os.environ.get("OPENAI_API_KEY")),
        "has_deepgram_key": bool(os.environ.get("DEEPGRAM_API_KEY")),
        "has_supabase_url": bool(os.environ.get("SUPABASE_URL"))
    }


__all__ = ['get_logger', 'create_session_logger', 'get_environment_info'] 