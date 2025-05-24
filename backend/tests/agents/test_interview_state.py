"""
Test cases for agents.interview_state module.
"""

import pytest
from backend.agents.interview_state import InterviewState, InterviewPhase


class TestInterviewPhase:
    """Test cases for InterviewPhase enum."""
    
    def test_phase_values_exist(self):
        """Test that all expected phase values exist."""
        expected_phases = ["initializing", "introducing", "questioning", "completed"]
        actual_phases = [phase.value for phase in InterviewPhase]
        
        for expected in expected_phases:
            assert expected in actual_phases
    
    def test_phase_enum_members(self):
        """Test that phase enum has expected members."""
        assert hasattr(InterviewPhase, 'INITIALIZING')
        assert hasattr(InterviewPhase, 'INTRODUCING')
        assert hasattr(InterviewPhase, 'QUESTIONING')
        assert hasattr(InterviewPhase, 'COMPLETED')


class TestInterviewState:
    """Test cases for InterviewState class."""
    
    def test_initial_state(self):
        """Test that InterviewState initializes with correct defaults."""
        state = InterviewState()
        
        assert state.phase == InterviewPhase.INITIALIZING
        assert state.initial_questions == []
        assert state.asked_question_count == 0
        assert state.current_question is None
        assert state.areas_covered == []
    
    def test_reset_functionality(self):
        """Test that reset() properly resets all state."""
        state = InterviewState()
        
        # Modify state
        state.phase = InterviewPhase.QUESTIONING
        state.initial_questions = ["Q1", "Q2"]
        state.asked_question_count = 5
        state.current_question = "Current question"
        state.areas_covered = ["topic1", "topic2"]
        
        # Reset and verify
        state.reset()
        
        assert state.phase == InterviewPhase.INITIALIZING
        assert state.initial_questions == []
        assert state.asked_question_count == 0
        assert state.current_question is None
        assert state.areas_covered == []
    
    def test_set_questions(self):
        """Test setting initial questions."""
        state = InterviewState()
        questions = ["Question 1", "Question 2", "Question 3"]
        
        state.set_questions(questions)
        
        assert state.initial_questions == questions
        assert len(state.initial_questions) == 3
    
    def test_ask_question(self):
        """Test asking a question updates state correctly."""
        state = InterviewState()
        question = "What is your experience with Python?"
        
        assert state.asked_question_count == 0
        assert state.current_question is None
        
        state.ask_question(question)
        
        assert state.asked_question_count == 1
        assert state.current_question == question
    
    def test_ask_multiple_questions(self):
        """Test asking multiple questions increments count correctly."""
        state = InterviewState()
        
        state.ask_question("Question 1")
        assert state.asked_question_count == 1
        assert state.current_question == "Question 1"
        
        state.ask_question("Question 2")
        assert state.asked_question_count == 2
        assert state.current_question == "Question 2"
    
    def test_add_covered_topics(self):
        """Test adding covered topics."""
        state = InterviewState()
        
        # Add initial topics
        topics1 = ["Python", "Django"]
        state.add_covered_topics(topics1)
        
        assert state.areas_covered == ["Python", "Django"]
        
        # Add more topics
        topics2 = ["JavaScript", "React"]
        state.add_covered_topics(topics2)
        
        assert state.areas_covered == ["Python", "Django", "JavaScript", "React"]
    
    def test_add_duplicate_topics(self):
        """Test that duplicate topics are not added."""
        state = InterviewState()
        
        # Add initial topics
        state.add_covered_topics(["Python", "Django"])
        assert len(state.areas_covered) == 2
        
        # Add duplicates
        state.add_covered_topics(["Python", "Flask"])
        
        # Should have Python only once
        assert state.areas_covered.count("Python") == 1
        assert "Flask" in state.areas_covered
        assert len(state.areas_covered) == 3
    
    def test_can_end_interview_insufficient_questions(self):
        """Test can_end_interview when not enough questions asked."""
        state = InterviewState()
        min_questions = 5
        
        # Ask fewer than minimum
        state.ask_question("Q1")
        state.ask_question("Q2")
        
        assert not state.can_end_interview(min_questions)
    
    def test_can_end_interview_sufficient_questions(self):
        """Test can_end_interview when enough questions asked."""
        state = InterviewState()
        min_questions = 3
        
        # Ask exactly minimum
        state.ask_question("Q1")
        state.ask_question("Q2")
        state.ask_question("Q3")
        
        assert state.can_end_interview(min_questions)
        
        # Ask more than minimum
        state.ask_question("Q4")
        assert state.can_end_interview(min_questions)
    
    def test_get_covered_topics_str_empty(self):
        """Test get_covered_topics_str with no topics."""
        state = InterviewState()
        
        result = state.get_covered_topics_str()
        assert result == "None"
    
    def test_get_covered_topics_str_with_topics(self):
        """Test get_covered_topics_str with topics."""
        state = InterviewState()
        
        state.add_covered_topics(["Python", "Django", "REST APIs"])
        
        result = state.get_covered_topics_str()
        assert result == "Python, Django, REST APIs"
    
    def test_state_independence(self):
        """Test that multiple InterviewState instances are independent."""
        state1 = InterviewState()
        state2 = InterviewState()
        
        state1.ask_question("Q1")
        state1.add_covered_topics(["Topic1"])
        
        # state2 should remain unaffected
        assert state2.asked_question_count == 0
        assert state2.areas_covered == []
        assert state2.current_question is None 