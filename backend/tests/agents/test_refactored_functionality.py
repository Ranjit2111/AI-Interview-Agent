"""
Integration tests for refactored agent functionality.
Tests that the agents work correctly after refactoring.
"""

import pytest
from backend.agents.interview_state import InterviewState, InterviewPhase
from backend.agents.constants import DEFAULT_JOB_ROLE, DEFAULT_COMPANY_NAME
from backend.utils.common import get_current_timestamp, safe_get_or_default


class TestRefactoredComponents:
    """Test refactored components independently."""
    
    def test_interview_state_integration(self):
        """Test that InterviewState works correctly with the refactored system."""
        state = InterviewState()
        
        # Test initial state
        assert state.phase == InterviewPhase.INITIALIZING
        assert state.asked_question_count == 0
        assert state.current_question is None
        assert state.areas_covered == []
        
        # Test state transitions
        state.phase = InterviewPhase.INTRODUCING
        state.ask_question("What is your experience with Python?")
        state.add_covered_topics(["Python", "Programming"])
        
        assert state.phase == InterviewPhase.INTRODUCING
        assert state.asked_question_count == 1
        assert state.current_question == "What is your experience with Python?"
        assert "Python" in state.areas_covered
        assert "Programming" in state.areas_covered
        
        # Test reset functionality
        state.reset()
        assert state.phase == InterviewPhase.INITIALIZING
        assert state.asked_question_count == 0
        assert state.current_question is None
        assert state.areas_covered == []
    
    def test_constants_integration(self):
        """Test that constants are properly integrated and accessible."""
        # Test that constants exist and are strings
        assert isinstance(DEFAULT_JOB_ROLE, str)
        assert isinstance(DEFAULT_COMPANY_NAME, str)
        assert len(DEFAULT_JOB_ROLE) > 0
        assert len(DEFAULT_COMPANY_NAME) > 0
        
        # Test that constants can be used in string formatting
        message = f"Welcome to {DEFAULT_COMPANY_NAME}! You're applying for {DEFAULT_JOB_ROLE}."
        assert DEFAULT_COMPANY_NAME in message
        assert DEFAULT_JOB_ROLE in message
    
    def test_utils_integration(self):
        """Test that utility functions work correctly."""
        # Test timestamp generation
        timestamp1 = get_current_timestamp()
        timestamp2 = get_current_timestamp()
        
        assert isinstance(timestamp1, str)
        assert isinstance(timestamp2, str)
        assert len(timestamp1) > 0
        assert len(timestamp2) > 0
        
        # Test safe_get_or_default
        assert safe_get_or_default("valid", "default") == "valid"
        assert safe_get_or_default("", "default") == "default"
        assert safe_get_or_default(None, "default") == "default"
    
    def test_question_templates_integration(self):
        """Test that question templates are properly structured."""
        from backend.agents.question_templates import QUESTION_TEMPLATES, GENERAL_QUESTIONS
        from backend.agents.config_models import InterviewStyle
        
        # Test that templates exist for all interview styles
        for style in InterviewStyle:
            assert style in QUESTION_TEMPLATES
            templates = QUESTION_TEMPLATES[style]
            assert isinstance(templates, list)
            assert len(templates) > 0
        
        # Test general questions
        assert isinstance(GENERAL_QUESTIONS, list)
        assert len(GENERAL_QUESTIONS) > 0
        
        # Test that questions can be formatted
        for question in GENERAL_QUESTIONS:
            try:
                formatted = question.format(job_role="Software Engineer")
                assert isinstance(formatted, str)
            except KeyError:
                # If no {job_role} placeholder, should work as-is
                assert "{job_role}" not in question
    
    def test_refactored_method_signatures(self):
        """Test that refactored methods have correct signatures by importing them."""
        # Test InterviewerAgent methods exist (without instantiation)
        from backend.agents.interviewer import InterviewerAgent
        
        # Check that the refactored methods exist as class methods
        assert hasattr(InterviewerAgent, '_generate_generic_questions')
        assert hasattr(InterviewerAgent, '_create_questions_from_templates')
        assert hasattr(InterviewerAgent, '_create_general_questions')
        assert hasattr(InterviewerAgent, '_can_generate_specific_questions')
        
        # Test AgenticCoachAgent methods exist (updated from CoachAgent)
        from backend.agents.agentic_coach import AgenticCoachAgent
        
        assert hasattr(AgenticCoachAgent, 'evaluate_answer')
        assert hasattr(AgenticCoachAgent, 'generate_final_summary_with_resources')
        assert hasattr(AgenticCoachAgent, '_setup_agentic_executor')
        
        # Test OrchestatorAgent methods exist
        from backend.agents.orchestrator import AgentSessionManager
        
        assert hasattr(AgentSessionManager, '_create_user_message')
        assert hasattr(AgentSessionManager, '_get_interviewer_response')
        assert hasattr(AgentSessionManager, '_generate_coaching_feedback')
        assert hasattr(AgentSessionManager, '_handle_processing_error')
        assert hasattr(AgentSessionManager, '_generate_final_coaching_summary')
    
    def test_imports_work_correctly(self):
        """Test that all refactored modules can be imported without errors."""
        # Test that all new modules can be imported
        from backend.agents.constants import DEFAULT_JOB_ROLE
        from backend.utils.common import get_current_timestamp
        from backend.agents.interview_state import InterviewState
        from backend.agents.question_templates import GENERAL_QUESTIONS
        
        # Test that main agents can still be imported
        from backend.agents.interviewer import InterviewerAgent
        from backend.agents.agentic_coach import AgenticCoachAgent
        from backend.agents.orchestrator import AgentSessionManager
        
        # Test that the agents module init works
        from backend.agents import InterviewerAgent as ImportedInterviewer
        from backend.agents import AgenticCoachAgent as ImportedCoach
        from backend.agents import AgentSessionManager as ImportedOrchestrator
        
        # Verify they're the same classes
        assert InterviewerAgent is ImportedInterviewer
        assert AgenticCoachAgent is ImportedCoach
        assert AgentSessionManager is ImportedOrchestrator
    
    def test_circular_imports_resolved(self):
        """Test that circular import issues have been resolved."""
        # This test passes if we can import all modules without circular import errors
        try:
            from backend.services import get_llm_service, get_event_bus, get_search_service
            from backend.agents import InterviewerAgent, AgenticCoachAgent, AgentSessionManager
            from backend.agents.constants import DEFAULT_JOB_ROLE
            from backend.utils.common import get_current_timestamp
            
            # If we get here without ImportError, circular imports are resolved
            assert True
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")
    
    def test_refactoring_completeness(self):
        """Test that refactoring removed the intended code bloat."""
        from backend.agents.interviewer import InterviewerAgent
        
        # Test that dead code was removed
        assert not hasattr(InterviewerAgent, '_format_response_by_style')
        assert not hasattr(InterviewerAgent, 'response_formatter_chain')
        
        # Test that long methods were broken down (by checking new methods exist)
        assert hasattr(InterviewerAgent, '_create_questions_from_templates')
        assert hasattr(InterviewerAgent, '_create_general_questions')
        assert hasattr(InterviewerAgent, '_can_generate_specific_questions')
        
        from backend.agents.agentic_coach import AgenticCoachAgent
        
        # Test that AgenticCoachAgent has required methods
        assert hasattr(AgenticCoachAgent, 'evaluate_answer')
        assert hasattr(AgenticCoachAgent, 'generate_final_summary_with_resources')
        
        from backend.agents.orchestrator import AgentSessionManager
        
        # Test that OrchestatorAgent has new helper methods
        assert hasattr(AgentSessionManager, '_create_user_message')
        assert hasattr(AgentSessionManager, '_handle_processing_error') 