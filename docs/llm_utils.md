# LLM Utility Functions Documentation

## Overview

This document outlines the utility functions that have been implemented to standardize LLM interactions across all agents in the system. These utilities provide robust error handling, consistent parsing, and simplified interfaces for common LLM operations.

## Key Utility Functions

### `invoke_chain_with_error_handling`

The primary function for safely invoking LangChain chains with comprehensive error handling.

```python
def invoke_chain_with_error_handling(
    chain,
    inputs: Dict[str, Any],
    default_creator: Callable[[], Any] = None,
    max_retries: int = 2,
    logger: Optional[logging.Logger] = None
) -> Any:
    """
    Invokes a LangChain chain with robust error handling.
    
    Args:
        chain: A LangChain chain to invoke
        inputs: Dictionary of inputs for the chain
        default_creator: Function that returns a default response on failure
        max_retries: Maximum number of retry attempts
        logger: Logger for recording errors
        
    Returns:
        The chain result or default response on failure
    """
```

#### Usage Example:

```python
# Example of using invoke_chain_with_error_handling
result = invoke_chain_with_error_handling(
    self.evaluation_chain,
    {
        "job_role": self.job_role,
        "question": question.text,
        "answer": answer_text,
        "question_type": question.question_type
    },
    default_creator=lambda: {
        "score": 3,
        "feedback": "I couldn't fully analyze your answer, but it was satisfactory.",
        "strengths": ["Attempted to answer the question"],
        "areas_of_improvement": ["Provide more specific details"]
    }
)
```

### `parse_json_with_fallback`

Safely parses JSON strings from LLM outputs with intelligent error recovery.

```python
def parse_json_with_fallback(
    json_string: str,
    default_value: Any,
    logger: Optional[logging.Logger] = None
) -> Any:
    """
    Attempts to parse a JSON string with fallback to default value.
    
    Args:
        json_string: JSON string to parse
        default_value: Value to return if parsing fails
        logger: Logger for recording errors
        
    Returns:
        Parsed JSON object or default value on failure
    """
```

#### Usage Example:

```python
# Example of using parse_json_with_fallback
thinking_result = parse_json_with_fallback(
    response_text,
    {
        "input_analysis": "Unable to analyze input",
        "key_topics": [],
        "sentiment": "neutral"
    },
    self.logger
)
```

### `extract_field_safely`

Extracts a field from a dictionary with type checking and default values.

```python
def extract_field_safely(
    data: Dict[str, Any],
    field_name: str,
    default_value: Any = None,
    expected_type: Optional[Type] = None
) -> Any:
    """
    Safely extracts a field from a dictionary with type checking.
    
    Args:
        data: Dictionary to extract from
        field_name: Name of the field to extract
        default_value: Value to return if field is missing or wrong type
        expected_type: Expected type of the field
        
    Returns:
        The field value or default value
    """
```

#### Usage Example:

```python
# Example of using extract_field_safely
score = extract_field_safely(evaluation, "score", 3, int)
feedback = extract_field_safely(evaluation, "feedback", "No specific feedback.", str)
strengths = extract_field_safely(evaluation, "strengths", [], list)
```

### `format_conversation_history`

Formats conversation history into a standardized string format for LLM context.

```python
def format_conversation_history(
    history: List[Dict[str, Any]],
    max_tokens: int = 2000,
    include_metadata: bool = False
) -> str:
    """
    Formats conversation history into a readable string.
    
    Args:
        history: List of conversation turn dictionaries
        max_tokens: Maximum token count to include
        include_metadata: Whether to include message metadata
        
    Returns:
        Formatted conversation history string
    """
```

#### Usage Example:

```python
# Example of using format_conversation_history
history_text = format_conversation_history(
    context.conversation_history,
    max_tokens=1500,
    include_metadata=False
)

prompt = f"""
Based on the following conversation history:

{history_text}

Generate the next response.
"""
```

### `clean_json_string`

Cleans and normalizes JSON strings from LLM outputs to improve parsing success.

```python
def clean_json_string(json_string: str) -> str:
    """
    Cleans a JSON string for more reliable parsing.
    
    Args:
        json_string: JSON string to clean
        
    Returns:
        Cleaned JSON string
    """
```

#### Usage Example:

```python
# Example of using clean_json_string
try:
    cleaned_json = clean_json_string(llm_output)
    parsed_data = json.loads(cleaned_json)
except json.JSONDecodeError:
    # Handle parsing failure
    parsed_data = default_value
```

## Integration with Agents

### In `BaseAgent` Class

The base agent implements common LLM interaction patterns using these utilities:

```python
def _call_llm(self, prompt: str, context: Optional[AgentContext] = None) -> str:
    """
    Calls the LLM with error handling.
    
    Args:
        prompt: The prompt to send to the LLM
        context: Optional agent context
        
    Returns:
        The LLM response string
    """
    try:
        # Create inputs for the LLM
        messages = []
        
        # Add system prompt if available
        system_prompt = self._get_system_prompt()
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        # Add conversation history if available
        if context and context.conversation_history:
            history_text = format_conversation_history(context.conversation_history)
            messages.append({"role": "user", "content": f"Conversation history:\n{history_text}"})
            
        # Add the current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Call LLM with retry logic
        result = self.llm.invoke(messages).content
        return result
    except Exception as e:
        self.logger.error(f"Error calling LLM: {e}")
        return "I encountered an error processing your request."
```

### Agent-Specific Implementation

Agents use the utilities to standardize their LLM interactions:

```python
def _process_answer(self, answer_text: str, context: AgentContext) -> dict:
    """Process and evaluate the candidate's answer."""
    
    # Create inputs for the template
    inputs = {
        "question": self.current_question.text,
        "answer": answer_text,
        "question_type": self.current_question.question_type,
        "job_role": self.job_role,
        "job_description": self.job_description
    }
    
    # Use the utility function for reliable LLM invocation
    evaluation = invoke_chain_with_error_handling(
        self.evaluation_chain,
        inputs,
        default_creator=lambda: {
            "score": 3,
            "feedback": "I couldn't fully analyze your answer, but it was satisfactory.",
            "strengths": ["Attempted to answer the question"],
            "areas_of_improvement": ["Provide more specific details"]
        },
        logger=self.logger
    )
    
    return evaluation
```

## Best Practices

### Use `invoke_chain_with_error_handling` for All Chain Calls

Always wrap chain invocations with this utility to ensure robust error handling:

```python
# ✅ DO THIS:
result = invoke_chain_with_error_handling(
    chain,
    inputs,
    default_creator=lambda: default_value
)

# ❌ NOT THIS:
try:
    result = chain.invoke(inputs)
except Exception as e:
    logger.error(f"Error: {e}")
    result = default_value
```

### Provide Meaningful Default Values

Default values should be structurally similar to successful responses:

```python
# ✅ DO THIS:
default_creator = lambda: {
    "score": 3,
    "feedback": "I couldn't fully analyze your answer.",
    "strengths": ["Attempted to answer"],
    "areas_of_improvement": ["Provide more details"]
}

# ❌ NOT THIS:
default_creator = lambda: None
# or
default_creator = lambda: "Error occurred"
```

### Log Errors Appropriately

Use the logger parameter to record detailed error information:

```python
# ✅ DO THIS:
result = invoke_chain_with_error_handling(
    chain,
    inputs,
    default_creator=lambda: default_value,
    logger=self.logger  # Pass the logger
)

# ❌ NOT THIS:
result = invoke_chain_with_error_handling(
    chain,
    inputs,
    default_creator=lambda: default_value
    # No logger provided
)
```

### Consistent JSON Parsing

Use `parse_json_with_fallback` for all JSON parsing from LLM outputs:

```python
# ✅ DO THIS:
result = parse_json_with_fallback(
    json_string,
    default_value,
    logger=self.logger
)

# ❌ NOT THIS:
try:
    result = json.loads(json_string)
except json.JSONDecodeError:
    result = default_value
```

## Common Patterns

### Chain Invocation Pattern

```python
def process_data(self, data: str) -> Dict[str, Any]:
    """Process data using an LLM chain."""
    
    # 1. Prepare inputs
    inputs = {
        "data": data,
        "parameters": self.parameters,
        "context": self.context
    }
    
    # 2. Define default response
    default_response = {
        "result": "Unable to process data completely",
        "confidence": 0.5,
        "suggestions": ["Try providing more details"]
    }
    
    # 3. Invoke chain with error handling
    result = invoke_chain_with_error_handling(
        self.processing_chain,
        inputs,
        default_creator=lambda: default_response,
        logger=self.logger
    )
    
    # 4. Post-process result if needed
    if "confidence" in result and result["confidence"] < 0.3:
        result["suggestions"].append("Consider rephrasing your input")
    
    return result
```

### JSON Processing Pattern

```python
def analyze_response(self, llm_output: str) -> Dict[str, Any]:
    """Analyze LLM output as JSON."""
    
    # 1. Define default structure
    default_analysis = {
        "main_points": [],
        "sentiment": "neutral",
        "action_items": []
    }
    
    # 2. Clean and parse JSON with fallback
    analysis = parse_json_with_fallback(
        llm_output,
        default_analysis,
        logger=self.logger
    )
    
    # 3. Extract and validate specific fields
    sentiment = extract_field_safely(analysis, "sentiment", "neutral", str)
    main_points = extract_field_safely(analysis, "main_points", [], list)
    
    # 4. Return validated structure
    return {
        "main_points": main_points[:3],  # Limit to top 3 points
        "sentiment": sentiment,
        "action_items": extract_field_safely(analysis, "action_items", [], list)
    }
```

## Future Enhancements

1. **Enhanced Error Recovery**
   - Implement more sophisticated error recovery strategies
   - Add automatic prompt reformulation on failure
   - Develop specialized parsers for different output formats

2. **Performance Monitoring**
   - Add success/failure metrics for LLM calls
   - Track latency and token usage
   - Identify problematic prompts and templates

3. **Output Validation**
   - Implement JSON schema validation for outputs
   - Add semantic validation for specific field types
   - Support automatic correction of minor errors in outputs

4. **Caching and Optimization**
   - Add result caching for repeated calls
   - Implement token optimization techniques
   - Support batched processing for efficiency 