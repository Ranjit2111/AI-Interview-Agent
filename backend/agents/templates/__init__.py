"""
Template definitions for agent interactions.
This module provides common templates for agent prompts, feedback formats, and responses.
"""

from backend.agents.templates.interviewer_templates import (
    INTERVIEWER_SYSTEM_PROMPT,
    NEXT_ACTION_TEMPLATE,
    JOB_SPECIFIC_TEMPLATE,
    INTRODUCTION_TEMPLATES
)

__all__ = [
    'INTERVIEWER_SYSTEM_PROMPT',
    'NEXT_ACTION_TEMPLATE',
    'JOB_SPECIFIC_TEMPLATE',
    'INTRODUCTION_TEMPLATES',
] 