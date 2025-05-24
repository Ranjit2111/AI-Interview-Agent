"""
Common utility functions used across the interview system.
"""

from datetime import datetime


def get_current_timestamp() -> str:
    """
    Get current UTC timestamp in ISO format.
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.utcnow().isoformat()


def safe_get_or_default(value: str, default: str) -> str:
    """
    Return value if not empty/None, otherwise return default.
    
    Args:
        value: The value to check
        default: Default value to return if value is empty
        
    Returns:
        value or default
    """
    return value if value else default 