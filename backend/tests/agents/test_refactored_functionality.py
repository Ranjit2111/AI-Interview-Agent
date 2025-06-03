"""
Test refactored functionality for agents.
This module tests the updated agent functionality after refactoring.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

# Core imports
from backend.agents.agentic_coach import AgenticCoachAgent
from backend.agents.interviewer import InterviewerAgent
from backend.agents.orchestrator import AgentSessionManager
from backend.services.llm_service import LLMService
from backend.services.search_service import SearchService
from backend.utils.event_bus import EventBus


class TestAgenticCoachFunctionality:
    """Test suite for the agentic coach functionality."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service for testing."""
        mock_service = Mock(spec=LLMService)
        mock_llm = Mock()
        mock_service.get_llm.return_value = mock_llm
        return mock_service
    
    @pytest.fixture
    def mock_search_service(self):
        """Mock search service for testing."""
        mock_service = Mock(spec=SearchService)
        mock_service.search_resources = AsyncMock(return_value=[])
        return mock_service
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus for testing."""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def agentic_coach(self, mock_llm_service, mock_search_service, mock_event_bus):
        """Create an agentic coach for testing."""
        return AgenticCoachAgent(
            llm_service=mock_llm_service,
            search_service=mock_search_service,
            event_bus=mock_event_bus,
            resume_content="Python developer with 2 years experience",
            job_description="Senior Python Developer position"
        )
    
    def test_agentic_coach_initialization(self, agentic_coach):
        """Test that the agentic coach initializes correctly."""
        assert agentic_coach is not None
        assert agentic_coach.search_service is not None
        assert agentic_coach.search_tool is not None
        assert agentic_coach.resume_content == "Python developer with 2 years experience"
        assert agentic_coach.job_description == "Senior Python Developer position"
    
    def test_agentic_coach_has_required_methods(self, agentic_coach):
        """Test that AgenticCoachAgent has required methods."""
        assert hasattr(agentic_coach, 'evaluate_answer')
        assert hasattr(agentic_coach, 'generate_final_summary_with_resources')
        assert hasattr(agentic_coach, 'process')
        assert hasattr(agentic_coach, '_build_evaluation_prompt')
        assert hasattr(agentic_coach, '_build_summary_prompt')
        assert hasattr(agentic_coach, '_parse_structured_summary')
    
    def test_agentic_coach_evaluate_answer(self, agentic_coach):
        """Test answer evaluation functionality."""
        result = agentic_coach.evaluate_answer(
            question="What is Python?",
            answer="Python is a programming language.",
            justification="Basic knowledge test",
            conversation_history=[]
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_agentic_coach_generate_summary(self, agentic_coach):
        """Test summary generation functionality."""
        conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi, let's start the interview"}
        ]
        
        result = agentic_coach.generate_final_summary_with_resources(conversation_history)
        
        assert isinstance(result, dict)
        assert "patterns_tendencies" in result
        assert "strengths" in result
        assert "weaknesses" in result
        assert "improvement_focus_areas" in result
        assert "recommended_resources" in result
        assert isinstance(result["recommended_resources"], list)


class TestAgentImports:
    """Test that agent imports work correctly."""
    
    def test_agent_imports(self):
        """Test that all agent classes can be imported."""
        from backend.agents import AgenticCoachAgent
        from backend.agents import InterviewerAgent
        from backend.agents import AgentSessionManager
        
        # Test that imports are the correct classes
        assert AgenticCoachAgent is not None
        assert InterviewerAgent is not None
        assert AgentSessionManager is not None


class TestAgentRegistry:
    """Test the agent registry functionality."""
    
    def test_agent_registry_structure(self):
        """Test that the agent registry has the correct structure."""
        from backend.agents import AGENT_REGISTRY
        
        assert isinstance(AGENT_REGISTRY, dict)
        assert 'interviewer' in AGENT_REGISTRY
        assert 'coach' in AGENT_REGISTRY
        
        # Verify that 'coach' points to AgenticCoachAgent
        from backend.agents.agentic_coach import AgenticCoachAgent
        assert AGENT_REGISTRY['coach'] is AgenticCoachAgent


class TestBackwardCompatibility:
    """Test that the refactoring maintains backward compatibility."""
    
    def test_coach_key_points_to_agentic_coach(self):
        """Test that the 'coach' key in registry points to AgenticCoachAgent."""
        from backend.agents import AGENT_REGISTRY
        from backend.agents.agentic_coach import AgenticCoachAgent
        
        assert AGENT_REGISTRY['coach'] is AgenticCoachAgent
    
    def test_orchestrator_compatibility(self):
        """Test that orchestrator can still create coach agents."""
        from backend.agents.orchestrator import AgentSessionManager
        from backend.agents.config_models import SessionConfig
        
        # This should not raise an error
        assert hasattr(AgentSessionManager, '_create_agent')


class TestModuleLevelFunctionality:
    """Test module-level functionality."""
    
    def test_module_exports(self):
        """Test that the module exports the correct items."""
        from backend.agents import __all__
        
        expected_exports = [
            'BaseAgent',
            'AgentContext', 
            'InterviewerAgent',
            'AgenticCoachAgent',
            'AgentSessionManager',
            'InterviewState',
            'InterviewPhase'
        ]
        
        for export in expected_exports:
            assert export in __all__ 