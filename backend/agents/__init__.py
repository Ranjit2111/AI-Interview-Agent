"""
Multi-agent system for AI interview preparation.
This module contains agents that collaborate to provide a comprehensive interview experience.
"""

from typing import Dict, Type

from .base import BaseAgent, AgentContext

from .interviewer import InterviewerAgent
from .agentic_coach import AgenticCoachAgent

from .orchestrator import AgentSessionManager
from .interview_state import InterviewState, InterviewPhase

__all__ = [
    'BaseAgent',
    'AgentContext',
    'InterviewerAgent',
    'AgenticCoachAgent',
    'AgentSessionManager',
    'InterviewState',
    'InterviewPhase'
]

AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    'interviewer': InterviewerAgent,
    'coach': AgenticCoachAgent,
} 