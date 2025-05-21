"""
Utility functions for agents, particularly for interacting with LLMs and processing data.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Callable, Union
import re

from langchain.chains.base import Chain


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
            processed_value = None
            key_found_and_processed = False # Flag to indicate successful processing

            # 1. Try direct output_key access
            if isinstance(result, dict) and output_key in result:
                extracted_value = result[output_key]
                logger.debug(f"Extracted value for direct output key '{output_key}': {str(extracted_value)[:100]}...")
                if isinstance(extracted_value, str):
                    # If the extracted value is a string, attempt to parse it as JSON.
                    # This handles cases where the chain is expected to output a JSON string under output_key.
                    parsed_json = parse_json_with_fallback(extracted_value, None, logger)
                    if parsed_json is not None:
                        processed_value = parsed_json
                    else:
                        # It's a string, but not JSON. Use the string value directly.
                        # This might happen if output_key is for a plain text field.
                        processed_value = extracted_value 
                else:
                    # It's not a string (e.g., already a dict/list from a Pydantic chain or other type).
                    # Use the extracted value as is.
                    processed_value = extracted_value
                key_found_and_processed = True
            
            # 2. Fallback: If output_key was not found, but 'text' key exists and might contain the desired JSON output.
            # This is common when the LLM directly returns a string that needs parsing, and Langchain wraps it in {"text": "..."}.
            elif isinstance(result, dict) and 'text' in result and isinstance(result['text'], str):
                logger.debug(f"Output key '{output_key}' not found directly. Attempting to parse JSON from 'text' field as a fallback for '{output_key}'.")
                parsed_json_from_text = parse_json_with_fallback(result['text'], None, logger)
                if parsed_json_from_text is not None:
                    processed_value = parsed_json_from_text
                    key_found_and_processed = True # Consider it found and processed if 'text' yielded valid JSON
                else:
                    # The 'text' field existed but was not valid JSON. 
                    # If the original output_key was expected to be a string (not JSON), 
                    # then result['text'] could be that string.
                    logger.warning(f"'text' field did not contain valid JSON. It might be a plain string. Value: {result['text'][:100]}...")
                    # Let's assume if we are here, we expected JSON. If 'text' is not JSON, it's likely not what we wanted for a JSON output_key.
                    # If output_key was for a non-JSON string, the first branch (direct access) should have handled it if the key existed.
                    # Thus, if 'text' is not JSON, we probably should fall through to error/default.
                    pass # Let it fall through to the error if key_found_and_processed is still False
            
            if key_found_and_processed:
                return processed_value
            else:
                logger.error(f"Output key '{output_key}' not found (and 'text' field fallback failed or was not applicable) in {chain_name} result: {result}")
                return default_value
        else: # No output_key specified (original logic)
            if isinstance(result, dict) and len(result) == 1:
                 first_value = next(iter(result.values()))
                 if isinstance(first_value, str):
                     # If the single value is a string, try to parse it as JSON
                     parsed_json = parse_json_with_fallback(first_value, None, logger)
                     if parsed_json is not None:
                         return parsed_json
            # Otherwise, return the full result (could be a dict with multiple keys, or a non-string single value)
            return result

    except Exception as e:
        logger.exception(f"Error invoking {chain_name}: {e}")
        return default_value
