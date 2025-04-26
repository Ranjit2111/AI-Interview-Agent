"""
Multi-agent system for AI interview preparation.
This module contains agents that collaborate to provide a comprehensive interview experience.
"""

from typing import Dict, Type

# Import base classes and components
from .base import BaseAgent, AgentContext

# Import specific agent implementations
from .interviewer import InterviewerAgent
from .coach import CoachAgent
from .skill_assessor import SkillAssessorAgent

# Import the session manager (previously orchestrator)
from .orchestrator import SessionManager

# Import supporting enums or data structures if needed by consumers
# (e.g., InterviewStyle might be useful, but often comes from models package)
# from ..models.interview import InterviewStyle 

# Define what is exposed when importing '*':
__all__ = [
    'BaseAgent',
    'AgentContext',
    'InterviewerAgent',
    'CoachAgent',
    'SkillAssessorAgent',
    'SessionManager'
]

# Optional: Agent registry for dynamic loading (if needed later)
AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    'interviewer': InterviewerAgent,
    'coach': CoachAgent,
    'skill_assessor': SkillAssessorAgent,
} 