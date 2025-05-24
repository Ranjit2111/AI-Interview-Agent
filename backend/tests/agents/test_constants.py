"""
Test cases for agents.constants module.
"""

import pytest
from backend.agents.constants import (
    DEFAULT_JOB_ROLE,
    DEFAULT_COMPANY_NAME,
    DEFAULT_VALUE_NOT_PROVIDED,
    DEFAULT_OPENING_QUESTION,
    DEFAULT_FALLBACK_QUESTION,
    MINIMUM_QUESTION_COUNT,
    ESTIMATED_TIME_PER_QUESTION,
    ERROR_AGENT_LOAD_FAILED,
    ERROR_INITIALIZATION_FAILED,
    ERROR_INTERVIEW_SETUP,
    ERROR_PROCESSING_REQUEST,
    ERROR_INTERVIEW_CONCLUDED,
    ERROR_NO_QUESTION_TEXT,
    INTERVIEW_CONCLUSION,
    LOG_GENERATING_QUESTIONS,
    LOG_INTERVIEW_INTRODUCTION,
    LOG_INTERVIEW_CONCLUDED,
    COACH_FEEDBACK_ERROR,
    COACH_FEEDBACK_UNAVAILABLE,
    COACH_FEEDBACK_NOT_GENERATED
)


class TestConstants:
    """Test cases for constants module."""
    
    def test_default_values_exist_and_not_empty(self):
        """Test that default values are defined and not empty."""
        assert DEFAULT_JOB_ROLE and isinstance(DEFAULT_JOB_ROLE, str)
        assert DEFAULT_COMPANY_NAME and isinstance(DEFAULT_COMPANY_NAME, str)
        assert DEFAULT_VALUE_NOT_PROVIDED and isinstance(DEFAULT_VALUE_NOT_PROVIDED, str)
    
    def test_question_constants_exist(self):
        """Test that question-related constants are defined."""
        assert DEFAULT_OPENING_QUESTION and isinstance(DEFAULT_OPENING_QUESTION, str)
        assert DEFAULT_FALLBACK_QUESTION and isinstance(DEFAULT_FALLBACK_QUESTION, str)
        assert isinstance(MINIMUM_QUESTION_COUNT, int) and MINIMUM_QUESTION_COUNT > 0
        assert isinstance(ESTIMATED_TIME_PER_QUESTION, int) and ESTIMATED_TIME_PER_QUESTION > 0
    
    def test_error_messages_exist(self):
        """Test that all error messages are defined."""
        error_constants = [
            ERROR_AGENT_LOAD_FAILED,
            ERROR_INITIALIZATION_FAILED,
            ERROR_INTERVIEW_SETUP,
            ERROR_PROCESSING_REQUEST,
            ERROR_INTERVIEW_CONCLUDED,
            ERROR_NO_QUESTION_TEXT
        ]
        
        for error_msg in error_constants:
            assert error_msg and isinstance(error_msg, str)
    
    def test_interview_conclusion_exists(self):
        """Test that interview conclusion message is defined."""
        assert INTERVIEW_CONCLUSION and isinstance(INTERVIEW_CONCLUSION, str)
    
    def test_log_messages_exist(self):
        """Test that logging messages are defined."""
        log_constants = [
            LOG_GENERATING_QUESTIONS,
            LOG_INTERVIEW_INTRODUCTION,
            LOG_INTERVIEW_CONCLUDED
        ]
        
        for log_msg in log_constants:
            assert log_msg and isinstance(log_msg, str)
    
    def test_coach_feedback_constants_exist(self):
        """Test that coach feedback constants are defined."""
        coach_constants = [
            COACH_FEEDBACK_ERROR,
            COACH_FEEDBACK_UNAVAILABLE,
            COACH_FEEDBACK_NOT_GENERATED
        ]
        
        for coach_msg in coach_constants:
            assert coach_msg and isinstance(coach_msg, str)
    
    def test_minimum_question_count_reasonable(self):
        """Test that minimum question count is reasonable."""
        assert 1 <= MINIMUM_QUESTION_COUNT <= 10  # Should be a reasonable minimum
    
    def test_estimated_time_per_question_reasonable(self):
        """Test that estimated time per question is reasonable."""
        assert 1 <= ESTIMATED_TIME_PER_QUESTION <= 10  # Should be reasonable time in minutes 