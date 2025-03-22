"""
Tests for the interview agent module.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.agents.interview import InterviewAgent


@pytest.fixture
def interview_agent():
    """Create an interview agent instance for testing."""
    return InterviewAgent()


@pytest.fixture
def mock_gemini():
    """Create a mock Gemini model."""
    with patch('backend.agents.interview.GoogleGenerativeAI') as mock:
        model = MagicMock()
        model.generate_content.return_value = MagicMock(
            text="Test interview response"
        )
        mock.return_value = model
        yield mock


class TestInterviewAgent:
    """Tests for the InterviewAgent class."""
    
    def test_initialization(self, interview_agent, mock_gemini):
        """Test that interview agent initializes properly."""
        assert interview_agent.model is not None
        assert interview_agent.context is not None
        assert interview_agent.current_question is None
        assert interview_agent.question_history == []
    
    def test_process_input(self, interview_agent, mock_gemini):
        """Test processing interview input."""
        # Test input
        test_input = "I have 5 years of Python experience"
        test_context = {"session_id": "test_session"}
        
        # Process input
        result = interview_agent.process_input(test_input, test_context)
        
        # Verify result
        assert result is not None
        assert "response" in result
        assert "next_question" in result
        assert "feedback" in result
        assert isinstance(result["response"], str)
        assert isinstance(result["next_question"], str)
        assert isinstance(result["feedback"], str)
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_question(self, interview_agent, mock_gemini):
        """Test question generation."""
        # Test context
        test_context = {
            "session_id": "test_session",
            "skills": ["Python", "SQL"],
            "experience": "5 years"
        }
        
        # Generate question
        question = interview_agent._generate_question(test_context)
        
        # Verify question
        assert question is not None
        assert isinstance(question, str)
        assert len(question) > 0
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_evaluate_response(self, interview_agent, mock_gemini):
        """Test response evaluation."""
        # Test data
        test_question = "Tell me about your Python experience"
        test_response = "I have 5 years of experience with Python"
        test_context = {"session_id": "test_session"}
        
        # Evaluate response
        evaluation = interview_agent._evaluate_response(
            test_question, test_response, test_context
        )
        
        # Verify evaluation
        assert evaluation is not None
        assert isinstance(evaluation, dict)
        assert "score" in evaluation
        assert "feedback" in evaluation
        assert 0 <= evaluation["score"] <= 1
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_update_question_history(self, interview_agent):
        """Test question history management."""
        # Add some questions
        interview_agent._update_question_history("Question 1")
        interview_agent._update_question_history("Question 2")
        
        # Verify history
        assert len(interview_agent.question_history) == 2
        assert interview_agent.question_history[0] == "Question 1"
        assert interview_agent.question_history[1] == "Question 2"
    
    def test_context_management(self, interview_agent):
        """Test context management in interview agent."""
        # Add some messages
        interview_agent.context.add_message("user", "Hello")
        interview_agent.context.add_message("assistant", "Hi there!")
        
        # Verify context state
        assert len(interview_agent.context.messages) == 2
        assert interview_agent.context.messages[0]["content"] == "Hello"
        assert interview_agent.context.messages[1]["content"] == "Hi there!"
    
    def test_error_handling(self, interview_agent, mock_gemini):
        """Test error handling in interview agent."""
        # Set up mock to raise an exception
        mock_gemini.return_value.generate_content.side_effect = Exception("Test error")
        
        # Test input
        test_input = "What's your experience?"
        test_context = {"session_id": "test_session"}
        
        # Process input (should handle error gracefully)
        result = interview_agent.process_input(test_input, test_context)
        
        # Verify error handling
        assert result is not None
        assert "error" in result
        assert isinstance(result["error"], str)
    
    def test_question_difficulty(self, interview_agent):
        """Test question difficulty adjustment."""
        # Test cases
        test_cases = [
            (0.8, "hard"),
            (0.6, "medium"),
            (0.4, "easy")
        ]
        
        for score, expected_difficulty in test_cases:
            difficulty = interview_agent._adjust_difficulty(score)
            assert difficulty == expected_difficulty
    
    def test_response_scoring(self, interview_agent):
        """Test response scoring logic."""
        # Test cases
        test_cases = [
            ("Excellent response", 0.9),
            ("Good response", 0.7),
            ("Average response", 0.5),
            ("Poor response", 0.3)
        ]
        
        for response, expected_score in test_cases:
            score = interview_agent._score_response(response)
            assert abs(score - expected_score) < 0.1
    
    def test_interview_progress(self, interview_agent):
        """Test interview progress tracking."""
        # Add some questions and responses
        interview_agent._update_question_history("Q1")
        interview_agent._update_question_history("Q2")
        interview_agent._update_question_history("Q3")
        
        # Verify progress
        assert interview_agent.get_progress() == 0.3  # 3 questions out of 10
        assert interview_agent.is_complete() is False
    
    def test_interview_completion(self, interview_agent):
        """Test interview completion."""
        # Add maximum questions
        for i in range(10):
            interview_agent._update_question_history(f"Q{i+1}")
        
        # Verify completion
        assert interview_agent.get_progress() == 1.0
        assert interview_agent.is_complete() is True


if __name__ == "__main__":
    pytest.main(["-v"]) 