# LLM Utilities

This document provides documentation for the utility functions used to interact with Large Language Models (LLMs) in the AI Interviewer Agent.

## Overview

The LLM utilities provide a consistent and robust way to interact with language models, handling common tasks such as error handling, JSON parsing, and structured output generation. These utilities are designed to simplify agent implementation and ensure consistent behavior across the application.

## Location

The LLM utilities are defined in `backend/agents/utils/llm_utils.py` and can be imported as:

```python
from backend.agents.utils.llm_utils import invoke_chain_with_error_handling, parse_json_with_fallback
```

## Core Functions

### `invoke_chain_with_error_handling`

This function provides a standardized way to invoke LLM chains with robust error handling.

**Signature:**

```python
def invoke_chain_with_error_handling(
    chain, 
    inputs, 
    default_creator=None, 
    max_retries=2,
    retry_delay=1,
    retry_backoff=2
):
    """Invoke an LLM chain with error handling and retries.
    
    Args:
        chain: The LLM chain to invoke
        inputs: The inputs to pass to the chain
        default_creator: A function that returns a default response if the chain fails
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries in seconds
        retry_backoff: Factor to increase delay on subsequent retries
        
    Returns:
        The chain result or the default response if the chain fails
    """
```

**Usage Example:**

```python
from backend.agents.utils.llm_utils import invoke_chain_with_error_handling

# Define a default creator function
def create_default_response():
    return {
        "score": 0,
        "feedback": "Unable to evaluate response due to a technical issue."
    }

# Invoke the chain with error handling
result = invoke_chain_with_error_handling(
    self.evaluation_chain,
    {
        "question": question,
        "response": user_response
    },
    default_creator=create_default_response
)
```

### `parse_json_with_fallback`

This function parses JSON strings with robust error handling and fallback mechanisms.

**Signature:**

```python
def parse_json_with_fallback(
    json_string, 
    default_value=None, 
    json_schema=None, 
    max_attempts=3
):
    """Parse a JSON string with fallback options and validation.
    
    Args:
        json_string: The JSON string to parse
        default_value: The default value to return if parsing fails
        json_schema: Optional JSON schema for validation
        max_attempts: Maximum number of attempts to fix and parse the JSON
        
    Returns:
        The parsed JSON object or the default value if parsing fails
    """
```

**Usage Example:**

```python
from backend.agents.utils.llm_utils import parse_json_with_fallback

# Define a JSON schema
schema = {
    "type": "object",
    "properties": {
        "score": {"type": "number"},
        "feedback": {"type": "string"}
    },
    "required": ["score", "feedback"]
}

# Parse JSON with schema validation
evaluation = parse_json_with_fallback(
    llm_response,
    default_value={"score": 0, "feedback": "Unable to parse evaluation."},
    json_schema=schema
)
```

## Additional Utilities

### `format_template_with_args`

This function formats a template string with provided arguments, safely handling missing keys.

**Signature:**

```python
def format_template_with_args(template, **kwargs):
    """Format a template string with provided arguments.
    
    Args:
        template: The template string to format
        **kwargs: The arguments to use for formatting
        
    Returns:
        The formatted template string
    """
```

**Usage Example:**

```python
from backend.agents.utils.llm_utils import format_template_with_args

formatted_prompt = format_template_with_args(
    QUESTION_TEMPLATE,
    role="Software Engineer",
    experience_level="Senior",
    skills=["Python", "JavaScript", "React"]
)
```

### `extract_json_from_text`

This function extracts JSON objects from unstructured text responses.

**Signature:**

```python
def extract_json_from_text(text):
    """Extract a JSON object from text response.
    
    Args:
        text: The text to extract JSON from
        
    Returns:
        The extracted JSON string or None if no JSON is found
    """
```

**Usage Example:**

```python
from backend.agents.utils.llm_utils import extract_json_from_text, parse_json_with_fallback

# Extract JSON from unstructured text
json_string = extract_json_from_text(llm_response)

# Parse the extracted JSON
if json_string:
    data = parse_json_with_fallback(json_string)
else:
    data = {"error": "No JSON found in response"}
```

## Error Handling Patterns

### Chain Invocation Pattern

```python
from backend.agents.utils.llm_utils import invoke_chain_with_error_handling

try:
    result = invoke_chain_with_error_handling(
        chain,
        inputs,
        default_creator=lambda: {"status": "error", "message": "Chain invocation failed"}
    )
    # Process successful result
except Exception as e:
    # Handle any uncaught exceptions
    logger.error(f"Unexpected error in chain invocation: {e}")
    result = {"status": "error", "message": "Unexpected error occurred"}
```

### JSON Parsing Pattern

```python
from backend.agents.utils.llm_utils import parse_json_with_fallback

def process_llm_response(response_text):
    # Attempt to parse the JSON response
    data = parse_json_with_fallback(
        response_text,
        default_value={"status": "error", "message": "Failed to parse response"}
    )
    
    # Validate required fields
    if "result" not in data:
        data["result"] = None
        data["status"] = "incomplete"
        
    return data
```

## Best Practices

1. **Always Use Error Handling**:
   - Use `invoke_chain_with_error_handling` for all LLM chain invocations
   - Provide meaningful default responses for failed chain invocations

2. **Structured Output Parsing**:
   - Use `parse_json_with_fallback` to handle inconsistent LLM outputs
   - Define JSON schemas for validation when possible
   - Provide sensible default values for parsing failures

3. **Timeout Management**:
   - Set appropriate timeout values for LLM calls
   - Implement retry logic with backoff for transient failures

4. **Logging**:
   - Log errors and warnings for failed LLM invocations
   - Include enough context to diagnose issues

5. **Testing**:
   - Write unit tests for utility functions
   - Test with various error scenarios
   - Mock LLM responses for consistent testing

## Common Issues and Solutions

### Issue: LLM Returns Malformed JSON

**Solution**: Use `parse_json_with_fallback` with appropriate default values:

```python
result = parse_json_with_fallback(
    llm_response,
    default_value={"status": "error", "message": "Invalid JSON response"}
)
```

### Issue: LLM Chain Fails Due to Rate Limiting

**Solution**: Use `invoke_chain_with_error_handling` with retry parameters:

```python
result = invoke_chain_with_error_handling(
    chain,
    inputs,
    max_retries=3,
    retry_delay=2,
    retry_backoff=2
)
```

### Issue: LLM Omits Required Fields

**Solution**: Validate the parsed response and add missing fields:

```python
data = parse_json_with_fallback(llm_response)
for field in ["score", "feedback", "recommendations"]:
    if field not in data:
        data[field] = None  # or appropriate default value
```

## Future Enhancements

- Enhanced JSON schema validation
- Support for streaming responses
- Performance monitoring and metrics
- More sophisticated retry policies
- Support for parallel LLM requests 