"""
Tests for the coach agent module.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.agents.coach import CoachAgent


@pytest.fixture
def coach_agent():
    """Create a coach agent instance for testing."""
    return CoachAgent()


@pytest.fixture
def mock_gemini():
    """Create a mock Gemini model."""
    with patch('backend.agents.coach.GoogleGenerativeAI') as mock:
        model = MagicMock()
        model.generate_content.return_value = MagicMock(
            text="Test coaching response"
        )
        mock.return_value = model
        yield mock


class TestCoachAgent:
    """Tests for the CoachAgent class."""
    
    def test_initialization(self, coach_agent, mock_gemini):
        """Test that coach agent initializes properly."""
        assert coach_agent.model is not None
        assert coach_agent.context is not None
        assert coach_agent.tools is not None
    
    def test_process_input(self, coach_agent, mock_gemini):
        """Test processing coaching input."""
        # Test input
        test_input = "How can I improve my coding skills?"
        test_context = {"session_id": "test_session"}
        
        # Process input
        result = coach_agent.process_input(test_input, test_context)
        
        # Verify result
        assert result is not None
        assert "response" in result
        assert "feedback" in result
        assert isinstance(result["response"], str)
        assert isinstance(result["feedback"], str)
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_coaching_response(self, coach_agent, mock_gemini):
        """Test generating coaching response."""
        # Test input
        test_input = "I'm struggling with Python decorators"
        test_context = {"session_id": "test_session"}
        
        # Generate response
        response = coach_agent._generate_coaching_response(test_input, test_context)
        
        # Verify response
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Verify model was called with correct prompt
        mock_gemini.return_value.generate_content.assert_called_once()
        call_args = mock_gemini.return_value.generate_content.call_args[0][0]
        assert "Python decorators" in call_args
    
    def test_generate_feedback(self, coach_agent, mock_gemini):
        """Test generating feedback."""
        # Test input
        test_input = "I'm struggling with Python decorators"
        test_context = {"session_id": "test_session"}
        
        # Generate feedback
        feedback = coach_agent._generate_feedback(test_input, test_context)
        
        # Verify feedback
        assert feedback is not None
        assert isinstance(feedback, str)
        assert len(feedback) > 0
        
        # Verify model was called with correct prompt
        mock_gemini.return_value.generate_content.assert_called_once()
        call_args = mock_gemini.return_value.generate_content.call_args[0][0]
        assert "feedback" in call_args.lower()
    
    def test_context_management(self, coach_agent):
        """Test context management in coach agent."""
        # Add some messages
        coach_agent.context.add_message("user", "Hello")
        coach_agent.context.add_message("assistant", "Hi there!")
        
        # Verify context state
        assert len(coach_agent.context.messages) == 2
        assert coach_agent.context.messages[0]["content"] == "Hello"
        assert coach_agent.context.messages[1]["content"] == "Hi there!"
    
    def test_error_handling(self, coach_agent, mock_gemini):
        """Test error handling in coach agent."""
        # Set up mock to raise an exception
        mock_gemini.return_value.generate_content.side_effect = Exception("Test error")
        
        # Test input
        test_input = "How can I improve?"
        test_context = {"session_id": "test_session"}
        
        # Process input (should handle error gracefully)
        result = coach_agent.process_input(test_input, test_context)
        
        # Verify error handling
        assert result is not None
        assert "error" in result
        assert isinstance(result["error"], str)
    
    def test_tool_usage(self, coach_agent):
        """Test using coaching tools."""
        # Test input requiring tool usage
        test_input = "What are some good Python learning resources?"
        test_context = {"session_id": "test_session"}
        
        # Process input
        result = coach_agent.process_input(test_input, test_context)
        
        # Verify result includes tool usage
        assert result is not None
        assert "response" in result
        assert "feedback" in result
        assert "resources" in result["response"].lower()
    
    def test_prompt_construction(self, coach_agent):
        """Test coaching prompt construction."""
        # Test input
        test_input = "I need help with async/await"
        test_context = {"session_id": "test_session"}
        
        # Get prompt
        prompt = coach_agent._construct_prompt(test_input, test_context)
        
        # Verify prompt
        assert prompt is not None
        assert isinstance(prompt, str)
        assert "async/await" in prompt
        assert "coach" in prompt.lower()
    
    def test_response_formatting(self, coach_agent, mock_gemini):
        """Test response formatting."""
        # Set up mock response
        mock_gemini.return_value.generate_content.return_value = MagicMock(
            text="Here's a formatted response:\n1. First point\n2. Second point"
        )
        
        # Test input
        test_input = "Format this response"
        test_context = {"session_id": "test_session"}
        
        # Process input
        result = coach_agent.process_input(test_input, test_context)
        
        # Verify formatting
        assert result is not None
        assert "response" in result
        assert "1. First point" in result["response"]
        assert "2. Second point" in result["response"]


if __name__ == "__main__":
    pytest.main(["-v"]) 