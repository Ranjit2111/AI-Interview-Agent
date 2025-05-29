"""
Configuration management for the AI Interviewer Agent.
Provides centralized configuration and logging setup.
"""
import logging

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