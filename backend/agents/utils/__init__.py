"""
Utility functions for agent operations.
This module provides common utilities for LLM interactions, error handling, and response formatting.
"""

try:
    # Try standard import in production
    from backend.agents.utils.llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback,
        extract_field_safely,
        format_conversation_history,
        calculate_average_scores
    )
except ImportError:
    # Use relative imports for development/testing
    from .llm_utils import (
        invoke_chain_with_error_handling,
        parse_json_with_fallback,
        extract_field_safely,
        format_conversation_history,
        calculate_average_scores
    )

__all__ = [
    'invoke_chain_with_error_handling',
    'parse_json_with_fallback',
    'extract_field_safely',
    'format_conversation_history',
    'calculate_average_scores'
] 