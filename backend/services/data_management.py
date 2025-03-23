"""
Data management service for interview sessions.
Provides functionality for archiving sessions and tracking metrics.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.interview import InterviewSession, Question, Answer, SkillAssessment
from backend.models.user import User
from backend.utils.event_bus import Event, EventBus


class DataManagementService:
    """
    Service for managing interview data, including archiving and metrics tracking.
    """
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the data management service.
        
        Args:
            event_bus: Event bus for subscribing to session events
            logger: Logger instance
        """
        self.event_bus = event_bus or EventBus()
        self.logger = logger or logging.getLogger(__name__)
        
        # Subscribe to relevant events
        if self.event_bus:
            self.event_bus.subscribe("interview_end", self._handle_interview_end)
            self.event_bus.subscribe("user_response", self._handle_user_response)
            self.event_bus.subscribe("agent_response", self._handle_agent_response)
    
    def archive_session(self, db: Session, session_id: str, conversation_history: List[Dict[str, Any]]) -> bool:
        """
        Archive an interview session to the database.
        
        Args:
            db: Database session
            session_id: Interview session ID
            conversation_history: List of conversation messages
            
        Returns:
            True if archiving was successful, False otherwise
        """
        try:
            # Get the existing session record
            session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
            
            if not session:
                self.logger.warning(f"Session {session_id} not found in database, cannot archive")
                return False
            
            # Extract questions and answers from conversation
            qa_pairs = self._extract_qa_pairs(conversation_history)
            
            # Store questions and answers
            for i, (question_text, answer_text) in enumerate(qa_pairs):
                # Create question
                question = Question(
                    interview_session_id=session_id,
                    text=question_text,
                    difficulty=3,  # Default medium difficulty
                    metadata={"position": i + 1},
                    created_at=datetime.utcnow()
                )
                db.add(question)
                db.flush()  # Get the question ID
                
                # Create answer
                answer = Answer(
                    question_id=question.id,
                    text=answer_text,
                    created_at=datetime.utcnow()
                )
                db.add(answer)
            
            db.commit()
            self.logger.info(f"Successfully archived session {session_id} with {len(qa_pairs)} Q&A pairs")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(f"Error archiving session {session_id}: {str(e)}")
            return False
    
    def calculate_session_metrics(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate metrics for an interview session.
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            Dictionary of metrics
        """
        # Extract basic metrics
        total_messages = len(conversation_history)
        user_messages = [msg for msg in conversation_history if msg.get("role") == "user"]
        assistant_messages = [msg for msg in conversation_history if msg.get("role") == "assistant"]
        
        # Calculate average response lengths
        avg_user_length = sum(len(msg.get("content", "")) for msg in user_messages) / max(len(user_messages), 1)
        avg_assistant_length = sum(len(msg.get("content", "")) for msg in assistant_messages) / max(len(assistant_messages), 1)
        
        # Calculate response times if timestamps are available
        response_times = []
        for i in range(1, len(conversation_history)):
            curr_msg = conversation_history[i]
            prev_msg = conversation_history[i-1]
            
            if "timestamp" in curr_msg and "timestamp" in prev_msg:
                try:
                    curr_time = datetime.fromisoformat(curr_msg["timestamp"])
                    prev_time = datetime.fromisoformat(prev_msg["timestamp"])
                    response_time = (curr_time - prev_time).total_seconds()
                    response_times.append(response_time)
                except (ValueError, TypeError):
                    pass
        
        avg_response_time = sum(response_times) / max(len(response_times), 1) if response_times else None
        
        # Return calculated metrics
        return {
            "total_messages": total_messages,
            "user_message_count": len(user_messages),
            "assistant_message_count": len(assistant_messages),
            "average_user_message_length": avg_user_length,
            "average_assistant_message_length": avg_assistant_length,
            "average_response_time_seconds": avg_response_time,
            "conversation_duration_seconds": (
                (datetime.fromisoformat(conversation_history[-1].get("timestamp", datetime.utcnow().isoformat())) - 
                 datetime.fromisoformat(conversation_history[0].get("timestamp", datetime.utcnow().isoformat()))).total_seconds()
                if len(conversation_history) > 1 and "timestamp" in conversation_history[0] and "timestamp" in conversation_history[-1]
                else None
            )
        }
    
    def _extract_qa_pairs(self, conversation_history: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
        """
        Extract question-answer pairs from conversation history.
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            List of (question, answer) tuples
        """
        qa_pairs = []
        for i in range(len(conversation_history) - 1):
            curr_msg = conversation_history[i]
            next_msg = conversation_history[i+1]
            
            # Look for assistant (interviewer) message followed by user message
            if (curr_msg.get("role") == "assistant" and 
                next_msg.get("role") == "user" and
                "interviewer" in curr_msg.get("agent", "")):
                
                question = curr_msg.get("content", "")
                answer = next_msg.get("content", "")
                
                # Only add if both question and answer exist
                if question and answer:
                    qa_pairs.append((question, answer))
        
        return qa_pairs
    
    def _handle_interview_end(self, event: Event) -> None:
        """
        Handle interview end events to archive the session.
        
        Args:
            event: The interview end event
        """
        self.logger.info(f"Received interview_end event for session {event.data.get('session_id')}")
        # Note: Actual archiving is done separately with DB access
    
    def _handle_user_response(self, event: Event) -> None:
        """
        Handle user response events for metrics tracking.
        
        Args:
            event: The user response event
        """
        # Update metrics as needed
        pass
    
    def _handle_agent_response(self, event: Event) -> None:
        """
        Handle agent response events for metrics tracking.
        
        Args:
            event: The agent response event
        """
        # Update metrics as needed
        pass 