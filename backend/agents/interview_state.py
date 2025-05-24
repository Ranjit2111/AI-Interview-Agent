"""
Interview state management for the InterviewerAgent.
"""

from typing import List, Optional
from enum import Enum


class InterviewPhase(Enum):
    """Enum representing the simplified states of an interview."""
    INITIALIZING = "initializing"
    INTRODUCING = "introducing"
    QUESTIONING = "questioning"
    COMPLETED = "completed"


class InterviewState:
    """
    Manages the state of an interview session.
    Encapsulates all state-related logic for cleaner agent code.
    """
    
    def __init__(self):
        self.phase = InterviewPhase.INITIALIZING
        self.initial_questions: List[str] = []
        self.asked_question_count = 0
        self.current_question: Optional[str] = None
        self.areas_covered: List[str] = []
    
    def reset(self) -> None:
        """Reset all state to initial values."""
        self.phase = InterviewPhase.INITIALIZING
        self.asked_question_count = 0
        self.initial_questions = []
        self.current_question = None
        self.areas_covered = []
    
    def set_questions(self, questions: List[str]) -> None:
        """Set the initial questions list."""
        self.initial_questions = questions
    
    def ask_question(self, question: str) -> None:
        """Record that a question was asked."""
        self.current_question = question
        self.asked_question_count += 1
    
    def add_covered_topics(self, topics: List[str]) -> None:
        """Add newly covered topics to the areas_covered list."""
        for topic in topics:
            if topic not in self.areas_covered:
                self.areas_covered.append(topic)
    
    def can_end_interview(self, min_questions: int) -> bool:
        """Check if interview can be ended based on question count."""
        return self.asked_question_count >= min_questions
    
    def get_covered_topics_str(self) -> str:
        """Get covered topics as a comma-separated string."""
        return ", ".join(self.areas_covered) if self.areas_covered else "None" 