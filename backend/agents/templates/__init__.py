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
        TIPS_TEMPLATE,
        TEMPLATE_PROMPT,
        STAR_EVALUATION_TEMPLATE,
        PERFORMANCE_ANALYSIS_TEMPLATE,
        COMMUNICATION_ASSESSMENT_TEMPLATE,
        COMPLETENESS_EVALUATION_TEMPLATE,
        PERSONALIZED_FEEDBACK_TEMPLATE,
        PERFORMANCE_METRICS_TEMPLATE,
        FEEDBACK_TEMPLATES,
        GENERAL_ADVICE_TEMPLATE,
        STAR_METHOD_ADVICE_TEMPLATE,
        SYSTEM_PROMPT as COACH_SYSTEM_PROMPT,
        PRACTICE_QUESTION_PROMPT,
        PRACTICE_QUESTION_RESPONSE_TEMPLATE
    )
    from backend.agents.templates.interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT as INTERVIEWER_SYSTEM_PROMPT,
        RESPONSE_FORMAT_TEMPLATE,
        NEXT_ACTION_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES
    )
    from backend.agents.templates.skill_templates import (
        SKILL_SYSTEM_PROMPT as SKILL_SYSTEM_PROMPT,
        SKILL_EXTRACTION_TEMPLATE,
        PROFICIENCY_ASSESSMENT_TEMPLATE,
        RESOURCE_SUGGESTION_TEMPLATE,
        SKILL_PROFILE_TEMPLATE
    )
except ImportError:
    # Use relative imports for development/testing
    from .coach_templates import (
        TIPS_TEMPLATE,
        TEMPLATE_PROMPT,
        STAR_EVALUATION_TEMPLATE,
        PERFORMANCE_ANALYSIS_TEMPLATE,
        COMMUNICATION_ASSESSMENT_TEMPLATE,
        COMPLETENESS_EVALUATION_TEMPLATE,
        PERSONALIZED_FEEDBACK_TEMPLATE,
        PERFORMANCE_METRICS_TEMPLATE,
        FEEDBACK_TEMPLATES,
        GENERAL_ADVICE_TEMPLATE,
        STAR_METHOD_ADVICE_TEMPLATE,
        SYSTEM_PROMPT as COACH_SYSTEM_PROMPT,
        PRACTICE_QUESTION_PROMPT,
        PRACTICE_QUESTION_RESPONSE_TEMPLATE
    )
    from .interviewer_templates import (
        INTERVIEWER_SYSTEM_PROMPT as INTERVIEWER_SYSTEM_PROMPT,
        RESPONSE_FORMAT_TEMPLATE,
        NEXT_ACTION_TEMPLATE,
        JOB_SPECIFIC_TEMPLATE,
        INTRODUCTION_TEMPLATES
    )
    from .skill_templates import (
        SKILL_SYSTEM_PROMPT as SKILL_SYSTEM_PROMPT,
        SKILL_EXTRACTION_TEMPLATE,
        PROFICIENCY_ASSESSMENT_TEMPLATE,
        RESOURCE_SUGGESTION_TEMPLATE,
        SKILL_PROFILE_TEMPLATE
    )

# Define __all__ based on the actual imported templates
__all__ = [
    # Coach templates
    'TIPS_TEMPLATE',
    'TEMPLATE_PROMPT',
    'STAR_EVALUATION_TEMPLATE',
    'PERFORMANCE_ANALYSIS_TEMPLATE',
    'COMMUNICATION_ASSESSMENT_TEMPLATE',
    'COMPLETENESS_EVALUATION_TEMPLATE',
    'PERSONALIZED_FEEDBACK_TEMPLATE',
    'PERFORMANCE_METRICS_TEMPLATE',
    'FEEDBACK_TEMPLATES',
    'GENERAL_ADVICE_TEMPLATE',
    'STAR_METHOD_ADVICE_TEMPLATE',
    'COACH_SYSTEM_PROMPT',
    'PRACTICE_QUESTION_PROMPT',
    'PRACTICE_QUESTION_RESPONSE_TEMPLATE',
    
    # Interviewer templates
    'INTERVIEWER_SYSTEM_PROMPT',
    'RESPONSE_FORMAT_TEMPLATE',
    'NEXT_ACTION_TEMPLATE',
    'JOB_SPECIFIC_TEMPLATE',
    'INTRODUCTION_TEMPLATES',
    
    # Skill assessor templates
    'SKILL_SYSTEM_PROMPT',
    'SKILL_EXTRACTION_TEMPLATE',
    'PROFICIENCY_ASSESSMENT_TEMPLATE',
    'RESOURCE_SUGGESTION_TEMPLATE',
    'SKILL_PROFILE_TEMPLATE'
] 