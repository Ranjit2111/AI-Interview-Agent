# Template System Documentation

## Overview

The template system is a core component of the AI Interviewer Agent architecture, providing a structured approach to prompt engineering and ensuring consistent interactions across all agents. This document outlines the design principles, organization, and best practices for working with templates in the system.

## Design Principles

The template system follows these key principles:

1. **Separation of Concerns**
   - Templates are separated from business logic
   - Prompt engineering changes don't require code changes
   - Templates can be modified independently of agent logic

2. **Centralization**
   - All templates for an agent type are centralized in dedicated files
   - Common patterns are standardized across different agents
   - Template reuse is encouraged for consistency

3. **Documentation**
   - All templates include inline documentation
   - Placeholder variables are clearly identified and explained
   - Expected output formats are specified

4. **Flexibility**
   - Import structure supports both production and development environments
   - Templates can be versioned and swapped easily
   - New template variants can be added without changing agent code

## Directory Structure

```
backend/
  └── agents/
      ├── templates/
      │   ├── __init__.py           # Exports all templates with proper namespacing
      │   ├── coach_templates.py    # Templates for the Coach agent
      │   ├── interviewer_templates.py # Templates for the Interviewer agent
      │   └── skill_templates.py    # Templates for the Skill Assessor agent
      └── utils/
          └── llm_utils.py          # Utilities for working with templates
```

## Template Organization

### By Agent Type

Templates are organized by agent type to maintain clear boundaries and facilitate targeted updates:

1. **coach_templates.py**
   - Templates for analyzing candidate responses
   - STAR method evaluation templates
   - Feedback generation templates
   - Practice question templates

2. **interviewer_templates.py**
   - System prompts for interviewer personality
   - Question generation templates
   - Answer evaluation templates
   - Interview summary templates

3. **skill_templates.py**
   - Skill identification templates
   - Proficiency assessment templates
   - Resource recommendation templates

### Template Categories

Within each agent's template file, templates are organized by functional category:

1. **System Prompts**
   - Define the agent's personality and role
   - Set constraints and style guidelines
   - Example: `INTERVIEWER_SYSTEM_PROMPT`, `COACH_SYSTEM_PROMPT`

2. **Analysis Templates**
   - Used to analyze candidate responses
   - Extract structured information from unstructured text
   - Example: `THINK_TEMPLATE`, `STAR_EVALUATION_TEMPLATE`

3. **Generation Templates**
   - Used to generate new content
   - Questions, feedback, recommendations
   - Example: `QUESTION_TEMPLATE`, `PRACTICE_QUESTION_PROMPT`

4. **Response Templates**
   - Format responses to the user
   - Standardize tone and structure
   - Example: `RESPONSE_FORMAT_TEMPLATE`

## Template Structure

Each template follows a standard pattern:

```python
# Template name with clear purpose
TEMPLATE_NAME = """
[Optional documentation about the template purpose and usage]

[Context for the LLM about its role and task]

[Input section with placeholders: {placeholder_name}]

[Thinking/reasoning guidelines for the LLM]

[Output format specification - often JSON structure]
"""
```

### Example Template:

```python
# Template for evaluating answer quality
ANSWER_EVALUATION_TEMPLATE = """
You are evaluating a candidate's answer for a {job_role} position.

Question: {question}
Candidate's Answer: {answer}
Question Type: {question_type}
Job Description: {job_description}
Evaluation Rubric: {rubric}

TASK: Evaluate the answer comprehensively and provide structured feedback.

THINK:
- How well did the answer address the specific question?
- What technical knowledge or soft skills were demonstrated?
- How structured and clear was the response?
- Were specific examples or experiences provided?
- What was missing that would have strengthened the answer?

OUTPUT - Provide your evaluation in JSON format with these fields:
{
    "score": 1-10 rating of overall quality,
    "feedback": "Detailed explanation of the evaluation with specific points",
    "strengths": ["List of 2-3 specific strengths demonstrated"],
    "areas_of_improvement": ["List of 2-3 specific areas to improve"],
    "questions_to_probe_further": ["Optional follow-up questions if needed"]
}

Ensure your evaluation is fair, constructive, and aligned with industry expectations for the {job_role} position.
"""
```

## Template Usage

### Import Structure

Templates are imported through a standardized pattern that supports both production and development environments:

```python
try:
    # Try standard import in production
    from backend.agents.templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT,
        QUESTION_TEMPLATE,
        # ... other imports
    )
except ImportError:
    # Use relative imports for development/testing
    from .templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT,
        QUESTION_TEMPLATE,
        # ... other imports
    )
```

### In Agent Code

Templates are used with the LLM via dedicated utility functions:

```python
# Using a template with an LLM
inputs = {
    "job_role": self.job_role,
    "question": question,
    "answer": answer_text
}

# Recommended approach using utility function
result = invoke_chain_with_error_handling(
    self.evaluation_chain,
    inputs,
    default_creator=lambda: {"score": 3, "feedback": "Default feedback"}
)

# Alternative direct approach
formatted_template = EVALUATION_TEMPLATE.format(**inputs)
response = self._call_llm(formatted_template, context)
```

## Best Practices

1. **Template Naming**
   - Use UPPERCASE for template constants
   - Make names descriptive of purpose
   - Use consistent naming patterns across agent types

2. **Placeholders**
   - Document all placeholders at the top of template files
   - Use descriptive names that match variable names in code
   - Keep placeholders consistent across related templates

3. **Output Formats**
   - Specify output format clearly in the template
   - Prefer structured outputs (JSON) for machine parsing
   - Include examples for complex formats

4. **Documentation**
   - Document the purpose of each template
   - Explain expected inputs and outputs
   - Include examples of good and bad usage

5. **Modifying Templates**
   - Test template changes thoroughly before deployment
   - Keep old versions when making significant changes
   - Update all dependent code when changing template structure

## Common Patterns

1. **Think-Then-Output Pattern**
   ```
   THINK:
   - [Guided thinking points for the LLM]
   
   OUTPUT:
   [Structured output format specification]
   ```

2. **JSON Output Pattern**
   ```
   OUTPUT - Provide your analysis in JSON format with these fields:
   {
       "field1": "description of value",
       "field2": ["array", "of", "values"],
       "field3": numeric_value
   }
   ```

3. **System Role Pattern**
   ```
   You are a [role description] for a {job_role} position.
   
   Your task is to [task description].
   ```

## Extending the Template System

To add new templates:

1. Add the template to the appropriate `*_templates.py` file
2. Update the import list in `templates/__init__.py`
3. Add the template name to the `__all__` list in `templates/__init__.py`
4. Use the template in agent code with proper error handling

## Template Migration

When migrating existing code to use templates:

1. Identify all string literals used with LLMs
2. Extract them to the appropriate template file
3. Add proper documentation and placeholder formatting
4. Replace string literals with template references
5. Update imports and verify functionality

## Future Enhancements

1. **Template Versioning**
   - Version templates for controlled updates
   - Support A/B testing of different prompts
   - Track performance metrics by template version

2. **Dynamic Templates**
   - Support dynamic template composition
   - Allow template chaining and inheritance
   - Implement template registries for plugin-style extensions

3. **Template Management UI**
   - Provide an interface for viewing and editing templates
   - Support non-technical users in prompt engineering
   - Visualize template relationships and dependencies 