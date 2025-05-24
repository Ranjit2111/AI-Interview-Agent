"""
LLM Chain processing helper class.
Extracts the complex chain invocation and result processing logic.
"""

import json
import logging
from typing import Dict, Any, Optional, Callable, Union
import re
from langchain.chains.base import Chain


class ChainResultProcessor:
    """Handles processing of LLM chain results with error handling."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def invoke_with_error_handling(
        self,
        chain: Chain,
        inputs: Dict[str, Any],
        chain_name: str = "LLM Chain",
        output_key: Optional[str] = None,
        default_creator: Optional[Callable[[], Any]] = None
    ) -> Optional[Any]:
        """
        Invokes a LangChain chain with robust error handling and logging.

        Args:
            chain: The LangChain chain instance to invoke.
            inputs: The input dictionary for the chain.
            chain_name: Name of the chain for logging purposes.
            output_key: If specified, returns only the value associated with this key from the result.
            default_creator: A function that returns a default value if the chain fails.

        Returns:
            The result of the chain invocation or default value on error.
        """
        default_value = default_creator() if default_creator else None
        
        try:
            self.logger.debug(f"Invoking {chain_name} with inputs: {json.dumps(inputs)[:200]}...")
            result = chain.invoke(inputs)
            self.logger.debug(f"{chain_name} invocation successful.")

            if not result:
                self.logger.warning(f"{chain_name} returned an empty result.")
                return default_value

            # Process result based on whether output_key is specified
            if output_key:
                return self._extract_output_key(result, output_key, default_value)
            else:
                return self._process_full_result(result)

        except Exception as e:
            self.logger.exception(f"Error invoking {chain_name}: {e}")
            return default_value
    
    def _extract_output_key(self, result: Any, output_key: str, default_value: Any) -> Any:
        """Extract specific output key from chain result."""
        # Try direct output_key access
        if isinstance(result, dict) and output_key in result:
            extracted_value = result[output_key]
            self.logger.debug(f"Extracted value for output key '{output_key}': {str(extracted_value)[:100]}...")
            return self._process_extracted_value(extracted_value)
        
        # Fallback: Try parsing JSON from 'text' field
        if isinstance(result, dict) and 'text' in result and isinstance(result['text'], str):
            self.logger.debug(f"Output key '{output_key}' not found. Attempting to parse JSON from 'text' field.")
            parsed_json = self._parse_json_with_fallback(result['text'])
            if parsed_json is not None:
                return parsed_json
            
            self.logger.warning(f"'text' field did not contain valid JSON. Value: {result['text'][:100]}...")
        
        self.logger.error(f"Output key '{output_key}' not found in result: {result}")
        return default_value
    
    def _process_extracted_value(self, value: Any) -> Any:
        """Process an extracted value, handling string JSON parsing."""
        if isinstance(value, str):
            # Try to parse as JSON if it's a string
            parsed_json = self._parse_json_with_fallback(value)
            return parsed_json if parsed_json is not None else value
        
        # Return as-is for non-string values
        return value
    
    def _process_full_result(self, result: Any) -> Any:
        """Process the full result when no output_key is specified."""
        if isinstance(result, dict) and len(result) == 1:
            first_value = next(iter(result.values()))
            if isinstance(first_value, str):
                # Try to parse single string value as JSON
                parsed_json = self._parse_json_with_fallback(first_value)
                if parsed_json is not None:
                    return parsed_json
        
        # Return the full result
        return result
    
    def _parse_json_with_fallback(self, json_string: str) -> Optional[Any]:
        """Parse JSON string with fallback handling."""
        try:
            # Try extracting JSON from markdown code block
            match = re.search(r"```(json)?\n(.*?)\n```", json_string, re.DOTALL | re.IGNORECASE)
            if match:
                json_string_extracted = match.group(2).strip()
                self.logger.debug(f"Extracted JSON from markdown block: {json_string_extracted[:100]}...")
                return json.loads(json_string_extracted)
            else:
                self.logger.debug(f"Attempting to parse JSON directly: {json_string[:100]}...")
                return json.loads(json_string)
                
        except json.JSONDecodeError as e:
            self.logger.debug(f"JSON parsing failed: {e}. String was: {json_string[:200]}...")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during JSON parsing: {e}")
            return None


def create_chain_processor(logger: logging.Logger) -> ChainResultProcessor:
    """Create a ChainResultProcessor instance."""
    return ChainResultProcessor(logger) 