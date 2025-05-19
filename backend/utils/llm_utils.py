"""
Utility functions for agents, particularly for interacting with LLMs and processing data.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Callable, Union
import re

from langchain.chains.base import Chain


def format_conversation_history(history: List[Dict[str, Any]]) -> str:
    """Formats conversation history into a readable string for LLM prompts."""
    formatted = []
    for msg in history:
        role = msg.get('role', 'unknown').capitalize()
        content = msg.get('content', '')
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

    Args:
        chain: The LangChain chain instance to invoke.
        inputs: The input dictionary for the chain.
        logger: The logger instance.
        chain_name: Name of the chain for logging purposes.
        output_key: If specified, returns only the value associated with this key from the result.
        default_creator: A function that returns a default value if the chain fails or output is invalid.
                       If None, returns None on failure.

    Returns:
        The result of the chain invocation (or specific value if output_key is set),
        or the result of default_creator() or None on error.
    """
    default_value = default_creator() if default_creator else None
    try:
        logger.debug(f"Invoking {chain_name} with inputs: {json.dumps(inputs)[:200]}...")
        result = chain.invoke(inputs)
        logger.debug(f"{chain_name} invocation successful.")

        if not result:
             logger.warning(f"{chain_name} returned an empty result.")
             return default_value

        if output_key:
            if isinstance(result, dict) and output_key in result:
                extracted_value = result[output_key]
                logger.debug(f"Extracted output key '{output_key}': {str(extracted_value)[:100]}...")
                if isinstance(extracted_value, str):
                    parsed_json = parse_json_with_fallback(extracted_value, None, logger)
                    if parsed_json is not None:
                        return parsed_json
                return extracted_value
            else:
                logger.error(f"Output key '{output_key}' not found in {chain_name} result: {result}")
                return default_value
        else:
            if isinstance(result, dict) and len(result) == 1:
                 first_value = next(iter(result.values()))
                 if isinstance(first_value, str):
                     parsed_json = parse_json_with_fallback(first_value, None, logger)
                     if parsed_json is not None:
                         return parsed_json
            return result

    except Exception as e:
        logger.exception(f"Error invoking {chain_name}: {e}")
        return default_value
