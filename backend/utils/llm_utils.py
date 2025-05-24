"""
Utility functions for agents, particularly for interacting with LLMs and processing data.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Callable, Union
import re

from langchain.chains.base import Chain
from .llm_chain_processor import create_chain_processor


def format_conversation_history(
    history: List[Dict[str, Any]],
    max_messages: Optional[int] = None,
    max_content_length: Optional[int] = None
) -> str:
    """Formats conversation history into a readable string for LLM prompts,
    with optional truncation by message count and content length."""
    formatted = []
    
    # Apply max_messages truncation (from the end, keeping most recent)
    if max_messages is not None and len(history) > max_messages:
        history_to_format = history[-max_messages:]
    else:
        history_to_format = history

    for msg in history_to_format:
        role = msg.get('role', 'unknown').capitalize()
        content = msg.get('content', '')
        
        # Apply max_content_length truncation to individual messages
        if max_content_length is not None and len(content) > max_content_length:
            content = content[:max_content_length] + "... (truncated)"
            
        formatted.append(f"{role}: {content}")
    return "\n\n".join(formatted)


def parse_json_with_fallback(json_string: str, default_value: Any, logger: logging.Logger) -> Any:
    """Safely parses a JSON string, returning a default value on failure."""
    try:
        match = re.search(r"```(json)?\n(.*?)\n```", json_string, re.DOTALL | re.IGNORECASE)
        if match:
            json_string_extracted = match.group(2).strip()
            logger.debug(f"Extracted JSON from markdown block: {json_string_extracted[:100]}...")
            return json.loads(json_string_extracted)
        else:
            logger.debug(f"Attempting to parse JSON directly: {json_string[:100]}...")
            return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}. String was: {json_string[:200]}... Returning default.")
        return default_value
    except Exception as e:
        logger.error(f"Unexpected error during JSON parsing: {e}. Returning default.")
        return default_value


def invoke_chain_with_error_handling(
    chain: Chain,
    inputs: Dict[str, Any],
    logger: logging.Logger,
    chain_name: str = "LLM Chain",
    output_key: Optional[str] = None,
    default_creator: Optional[Callable[[], Any]] = None
) -> Optional[Any]:
    """
    Invokes a LangChain chain with robust error handling and logging.
    
    Note: This function is refactored to use ChainResultProcessor for better maintainability.

    Args:
        chain: The LangChain chain instance to invoke.
        inputs: The input dictionary for the chain.
        logger: The logger instance.
        chain_name: Name of the chain for logging purposes.
        output_key: If specified, returns only the value associated with this key from the result.
        default_creator: A function that returns a default value if the chain fails.

    Returns:
        The result of the chain invocation or default value on error.
    """
    processor = create_chain_processor(logger)
    return processor.invoke_with_error_handling(
        chain=chain,
        inputs=inputs,
        chain_name=chain_name,
        output_key=output_key,
        default_creator=default_creator
    )
