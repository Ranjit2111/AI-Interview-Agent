"""
Multi-agent system for AI interview preparation.
This module contains agents that collaborate to provide a comprehensive interview experience.
"""

try:
    # Try standard import in production
    from backend.agents.base import BaseAgent, AgentContext
    from backend.agents.interviewer import InterviewerAgent, InterviewState
    from backend.agents.coach import CoachAgent, CoachingFocus
    from backend.agents.skill_assessor import SkillAssessorAgent, ProficiencyLevel, SkillCategory
    from backend.agents.orchestrator import AgentOrchestrator, OrchestratorMode
except ImportError:
    # Use relative imports for development/testing
    from .base import BaseAgent, AgentContext
    from .interviewer import InterviewerAgent, InterviewState
    from .coach import CoachAgent, CoachingFocus
    from .skill_assessor import SkillAssessorAgent, ProficiencyLevel, SkillCategory
    from .orchestrator import AgentOrchestrator, OrchestratorMode

__all__ = [
    'BaseAgent',
    'AgentContext',
    'InterviewerAgent',
    'InterviewState',
    'CoachAgent',
    'CoachingFocus',
    'SkillAssessorAgent',
    'ProficiencyLevel',
    'SkillCategory',
    'AgentOrchestrator',
    'OrchestratorMode'
] 