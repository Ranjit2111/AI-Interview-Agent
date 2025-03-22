"""
Utility functions for working with Language Models.

This module contains common utility functions for LLM operations,
error handling, response parsing, and data formatting.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable


def invoke_chain_with_error_handling(
    chain: Any,
    inputs: Dict[str, Any],
    output_key: str,
    default_creator: Callable[[], Dict[str, Any]],
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Invoke an LLM chain with standardized error handling.
    
    Args:
        chain: The LangChain chain to invoke
        inputs: The inputs to pass to the chain
        output_key: The key for the output in the response
        default_creator: Function that creates a default response
        logger: Optional logger for error messages
        
    Returns:
        The parsed response or a default value on error
    """
    try:
        # Call LLM chain
        response = chain.invoke(inputs)
        
        # Parse the response
        if isinstance(response, dict) and output_key in response:
            result = response[output_key]
            try:
                if isinstance(result, str):
                    # Try to parse the string as JSON
                    result = json.loads(result)
                return result
            except json.JSONDecodeError:
                if logger:
                    logger.error(f"Failed to parse {output_key} as JSON")
                return default_creator()
        else:
            if logger:
                logger.error(f"Response missing {output_key}")
            return default_creator()
    except Exception as e:
        if logger:
            logger.error(f"Error in chain invocation: {e}")
        return default_creator()


def parse_json_with_fallback(
    json_string: str,
    default_value: Any,
    logger: Optional[logging.Logger] = None
) -> Any:
    """
    Attempt to parse a JSON string and return a default value if parsing fails.
    
    Args:
        json_string: The JSON string to parse
        default_value: The value to return if parsing fails
        logger: Optional logger for error messages
        
    Returns:
        The parsed JSON or the default value
    """
    try:
        # Strip any potential markdown code block markers
        if "```json" in json_string:
            # Extract content between ```json and ```
            parts = json_string.split("```json", 1)
            if len(parts) > 1:
                json_content = parts[1].split("```", 1)[0].strip()
                return json.loads(json_content)
        
        # Try to parse as regular JSON
        return json.loads(json_string)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        if logger:
            logger.error(f"JSON parsing error: {e}")
        return default_value


def extract_field_safely(
    data: Dict[str, Any],
    field_path: str,
    default_value: Any = None
) -> Any:
    """
    Safely extract a field from a nested dictionary using dot notation.
    
    Args:
        data: The dictionary to extract from
        field_path: The path to the field using dot notation (e.g., "user.profile.name")
        default_value: The value to return if the field does not exist
        
    Returns:
        The field value or the default value
    """
    try:
        # Split the path into individual keys
        keys = field_path.split('.')
        result = data
        
        # Navigate through the nested structure
        for key in keys:
            if isinstance(result, dict) and key in result:
                result = result[key]
            else:
                return default_value
                
        return result
    except Exception:
        return default_value


def format_conversation_history(
    messages: List[Dict[str, str]],
    max_messages: int = 10
) -> str:
    """
    Format conversation messages into a string suitable for LLM context.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        max_messages: Maximum number of recent messages to include
        
    Returns:
        Formatted conversation history string
    """
    # Take only the most recent messages if there are too many
    if len(messages) > max_messages:
        messages = messages[-max_messages:]
    
    # Format each message
    formatted_messages = []
    for msg in messages:
        role = msg.get('role', 'unknown').capitalize()
        content = msg.get('content', '')
        formatted_messages.append(f"{role}: {content}")
    
    # Join messages with line breaks
    return "\n\n".join(formatted_messages)


def calculate_average_scores(
    evaluation: Dict[str, Any],
    score_fields: List[str] = None
) -> float:
    """
    Calculate the average score from multiple fields in an evaluation dictionary.
    
    Args:
        evaluation: The evaluation dictionary
        score_fields: List of field paths to scores using dot notation
        
    Returns:
        Average score (0-10) or 5.0 if no scores are found
    """
    # Default score fields to look for
    if score_fields is None:
        score_fields = [
            "situation.score", "task.score", "action.score", "result.score",
            "clarity.score", "conciseness.score", "structure.score", 
            "engagement.score", "confidence.score",
            "question_relevance.score", "key_points_coverage.score", 
            "examples.score", "depth.score", "context_awareness.score",
            "overall_score"
        ]
    
    # Extract available scores
    scores = []
    for field in score_fields:
        score = extract_field_safely(evaluation, field)
        if isinstance(score, (int, float)) and 0 <= score <= 10:
            scores.append(score)
    
    # Calculate average or return default
    if scores:
        return sum(scores) / len(scores)
    else:
        return 5.0  # Default middle score 