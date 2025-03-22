"""
Tests for the feedback agent module.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.agents.feedback import FeedbackAgent


@pytest.fixture
def feedback_agent():
    """Create a feedback agent instance for testing."""
    return FeedbackAgent()


@pytest.fixture
def mock_gemini():
    """Create a mock Gemini model."""
    with patch('backend.agents.feedback.GoogleGenerativeAI') as mock:
        model = MagicMock()
        model.generate_content.return_value = MagicMock(
            text="Test feedback response"
        )
        mock.return_value = model
        yield mock


class TestFeedbackAgent:
    """Tests for the FeedbackAgent class."""
    
    def test_initialization(self, feedback_agent, mock_gemini):
        """Test that feedback agent initializes properly."""
        assert feedback_agent.model is not None
        assert feedback_agent.context is not None
        assert feedback_agent.feedback_history == []
    
    def test_process_input(self, feedback_agent, mock_gemini):
        """Test processing feedback input."""
        # Test input
        test_input = "I need feedback on my interview performance"
        test_context = {
            "session_id": "test_session",
            "interview_data": {
                "questions": ["Q1", "Q2"],
                "responses": ["R1", "R2"],
                "scores": [0.8, 0.7]
            }
        }
        
        # Process input
        result = feedback_agent.process_input(test_input, test_context)
        
        # Verify result
        assert result is not None
        assert "feedback" in result
        assert "suggestions" in result
        assert "improvement_areas" in result
        assert isinstance(result["feedback"], str)
        assert isinstance(result["suggestions"], list)
        assert isinstance(result["improvement_areas"], list)
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_feedback(self, feedback_agent, mock_gemini):
        """Test feedback generation."""
        # Test data
        test_data = {
            "interview_data": {
                "questions": ["Q1", "Q2"],
                "responses": ["R1", "R2"],
                "scores": [0.8, 0.7]
            }
        }
        
        # Generate feedback
        feedback = feedback_agent._generate_feedback(test_data)
        
        # Verify feedback
        assert feedback is not None
        assert isinstance(feedback, dict)
        assert "feedback" in feedback
        assert "suggestions" in feedback
        assert "improvement_areas" in feedback
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_analyze_performance(self, feedback_agent, mock_gemini):
        """Test performance analysis."""
        # Test data
        test_data = {
            "scores": [0.8, 0.7, 0.9],
            "responses": ["R1", "R2", "R3"]
        }
        
        # Analyze performance
        analysis = feedback_agent._analyze_performance(test_data)
        
        # Verify analysis
        assert analysis is not None
        assert isinstance(analysis, dict)
        assert "strengths" in analysis
        assert "weaknesses" in analysis
        assert "average_score" in analysis
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_suggestions(self, feedback_agent, mock_gemini):
        """Test suggestion generation."""
        # Test data
        test_data = {
            "weaknesses": ["communication", "technical depth"],
            "improvement_areas": ["problem-solving", "code quality"]
        }
        
        # Generate suggestions
        suggestions = feedback_agent._generate_suggestions(test_data)
        
        # Verify suggestions
        assert suggestions is not None
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_context_management(self, feedback_agent):
        """Test context management in feedback agent."""
        # Add some messages
        feedback_agent.context.add_message("user", "Hello")
        feedback_agent.context.add_message("assistant", "Hi there!")
        
        # Verify context state
        assert len(feedback_agent.context.messages) == 2
        assert feedback_agent.context.messages[0]["content"] == "Hello"
        assert feedback_agent.context.messages[1]["content"] == "Hi there!"
    
    def test_error_handling(self, feedback_agent, mock_gemini):
        """Test error handling in feedback agent."""
        # Set up mock to raise an exception
        mock_gemini.return_value.generate_content.side_effect = Exception("Test error")
        
        # Test input
        test_input = "Give me feedback"
        test_context = {"session_id": "test_session"}
        
        # Process input (should handle error gracefully)
        result = feedback_agent.process_input(test_input, test_context)
        
        # Verify error handling
        assert result is not None
        assert "error" in result
        assert isinstance(result["error"], str)
    
    def test_feedback_history(self, feedback_agent):
        """Test feedback history management."""
        # Add some feedback
        feedback_agent._add_to_history("Feedback 1")
        feedback_agent._add_to_history("Feedback 2")
        
        # Verify history
        assert len(feedback_agent.feedback_history) == 2
        assert feedback_agent.feedback_history[0] == "Feedback 1"
        assert feedback_agent.feedback_history[1] == "Feedback 2"
    
    def test_score_analysis(self, feedback_agent):
        """Test score analysis functionality."""
        # Test cases
        test_cases = [
            ([0.8, 0.9, 0.7], 0.8, "strong"),
            ([0.6, 0.5, 0.7], 0.6, "moderate"),
            ([0.3, 0.4, 0.2], 0.3, "needs_improvement")
        ]
        
        for scores, expected_avg, expected_level in test_cases:
            analysis = feedback_agent._analyze_scores(scores)
            assert abs(analysis["average"] - expected_avg) < 0.1
            assert analysis["level"] == expected_level
    
    def test_feedback_formatting(self, feedback_agent, mock_gemini):
        """Test feedback formatting."""
        # Set up mock response
        mock_gemini.return_value.generate_content.return_value = MagicMock(
            text="Here's your feedback:\n1. First point\n2. Second point"
        )
        
        # Test input
        test_input = "Format this feedback"
        test_context = {"session_id": "test_session"}
        
        # Process input
        result = feedback_agent.process_input(test_input, test_context)
        
        # Verify formatting
        assert result is not None
        assert "feedback" in result
        assert "1. First point" in result["feedback"]
        assert "2. Second point" in result["feedback"]


if __name__ == "__main__":
    pytest.main(["-v"]) 