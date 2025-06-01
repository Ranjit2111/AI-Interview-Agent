"""
Multi-agent system for AI interview preparation.
This module contains agents that collaborate to provide a comprehensive interview experience.
"""

from typing import Dict, Type

from .base import BaseAgent, AgentContext

from .interviewer import InterviewerAgent
from .coach import CoachAgent
from .agentic_coach import AgenticCoachAgent

from .orchestrator import AgentSessionManager
from .interview_state import InterviewState, InterviewPhase

__all__ = [
    'BaseAgent',
    'AgentContext',
    'InterviewerAgent',
    'CoachAgent',
    'AgenticCoachAgent',
    'AgentSessionManager',
    'InterviewState',
    'InterviewPhase'
]

AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    'interviewer': InterviewerAgent,
    'coach': CoachAgent,
    'agentic_coach': AgenticCoachAgent,
} 