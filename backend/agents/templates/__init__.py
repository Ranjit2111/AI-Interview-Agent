# This __init__.py file can be intentionally left empty.
# Agents import directly from the specific template files (e.g., coach_templates.py).

"""
Template definitions for agent interactions.
This module provides common templates for agent prompts, feedback formats, and responses.
"""

# This __init__.py file primarily defines the __all__ list for easier imports,
# but agents can also import directly from the specific template files.

try:
    # Try standard import in production
    from backend.agents.templates.coach_templates import (
        EVALUATE_ANSWER_TEMPLATE,
        FINAL_SUMMARY_TEMPLATE
    )
    from backend.agents.templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT as INTERVIEWER_SYSTEM_PROMPT,
        RESPONSE_FORMAT_TEMPLATE,
        NEXT_ACTION_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES
    )
except ImportError:
    # Use relative imports for development/testing
    from .coach_templates import (
        EVALUATE_ANSWER_TEMPLATE,
        FINAL_SUMMARY_TEMPLATE
    )
    from .interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT as INTERVIEWER_SYSTEM_PROMPT,
        RESPONSE_FORMAT_TEMPLATE,
        NEXT_ACTION_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES
    )

# Define __all__ based on the actual imported templates
__all__ = [
    # Coach templates
    'EVALUATE_ANSWER_TEMPLATE',
    'FINAL_SUMMARY_TEMPLATE',
    
    # Interviewer templates
    'INTERVIEWER_SYSTEM_PROMPT',
    'RESPONSE_FORMAT_TEMPLATE',
    'NEXT_ACTION_TEMPLATE',
    'JOB_SPECIFIC_TEMPLATE',
    'INTRODUCTION_TEMPLATES',
] 