"""
Data management service for interview sessions.
Provides functionality for archiving sessions and tracking metrics.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.interview import InterviewSession, Question, Answer, SkillAssessment
from backend.models.user import User
from backend.utils.event_bus import Event, EventBus

# Define a cache TTL (time to live) in seconds
CACHE_TTL = 300  # 5 minute cache expiration

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
        
        # Initialize caches
        self._metrics_cache = {}
        self._metrics_cache_timestamps = {}
        self._qa_pairs_cache = {}
        self._qa_pairs_cache_timestamps = {}
        
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
            # Use a single query to get the session record
            session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
            
            if not session:
                self.logger.warning(f"Session {session_id} not found in database, cannot archive")
                return False
            
            # Extract questions and answers from conversation - use cached version if available
            qa_pairs = self._extract_qa_pairs_cached(conversation_history)
            
            # Batch database operations
            questions_to_add = []
            answers_to_add = []
            
            # Prepare questions and answers
            for i, (question_text, answer_text) in enumerate(qa_pairs):
                # Create question
                question = Question(
                    interview_session_id=session_id,
                    text=question_text,
                    difficulty=3,  # Default medium difficulty
                    metadata={"position": i + 1},
                    created_at=datetime.utcnow()
                )
                questions_to_add.append(question)
                
                # Will add answers after questions are inserted
            
            # Bulk insert questions
            if questions_to_add:
                db.bulk_save_objects(questions_to_add)
                db.flush()  # Make sure questions have IDs
            
                # Now create answers with question IDs
                for i, question in enumerate(questions_to_add):
                    _, answer_text = qa_pairs[i]
                    answer = Answer(
                        question_id=question.id,
                        text=answer_text,
                        created_at=datetime.utcnow()
                    )
                    answers_to_add.append(answer)
                
                # Bulk insert answers
                if answers_to_add:
                    db.bulk_save_objects(answers_to_add)
            
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
        # Check if metrics are cached
        cache_key = self._get_conversation_cache_key(conversation_history)
        now = datetime.utcnow()
        
        if (cache_key in self._metrics_cache and 
            cache_key in self._metrics_cache_timestamps and
            (now - self._metrics_cache_timestamps[cache_key]).total_seconds() < CACHE_TTL):
            return self._metrics_cache[cache_key]
        
        # Optimization: Pre-filter messages by role for faster processing
        user_messages = []
        assistant_messages = []
        total_messages = len(conversation_history)
        
        # Single pass through conversation history
        for msg in conversation_history:
            role = msg.get("role")
            if role == "user":
                user_messages.append(msg)
            elif role == "assistant":
                assistant_messages.append(msg)
        
        # Calculate average response lengths - use list comprehension for efficiency
        avg_user_length = sum(len(msg.get("content", "")) for msg in user_messages) / max(len(user_messages), 1)
        avg_assistant_length = sum(len(msg.get("content", "")) for msg in assistant_messages) / max(len(assistant_messages), 1)
        
        # Calculate response times if timestamps are available
        response_times = []
        timestamps = []
        
        # First extract all valid timestamps to avoid repeated parsing
        for msg in conversation_history:
            if "timestamp" in msg:
                try:
                    timestamp = datetime.fromisoformat(msg["timestamp"])
                    timestamps.append((msg.get("role"), timestamp))
                except (ValueError, TypeError):
                    timestamps.append((msg.get("role"), None))
            else:
                timestamps.append((msg.get("role"), None))
        
        # Now calculate time differences
        for i in range(1, len(timestamps)):
            curr_role, curr_time = timestamps[i]
            prev_role, prev_time = timestamps[i-1]
            
            if curr_time and prev_time:
                response_time = (curr_time - prev_time).total_seconds()
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / max(len(response_times), 1) if response_times else None
        
        # Calculate conversation duration
        conversation_duration = None
        if len(timestamps) > 1 and timestamps[0][1] and timestamps[-1][1]:
            conversation_duration = (timestamps[-1][1] - timestamps[0][1]).total_seconds()
        
        # Create metrics dictionary
        metrics = {
            "total_messages": total_messages,
            "user_message_count": len(user_messages),
            "assistant_message_count": len(assistant_messages),
            "average_user_message_length": avg_user_length,
            "average_assistant_message_length": avg_assistant_length,
            "average_response_time_seconds": avg_response_time,
            "conversation_duration_seconds": conversation_duration
        }
        
        # Cache the result
        self._metrics_cache[cache_key] = metrics
        self._metrics_cache_timestamps[cache_key] = now
        
        return metrics
    
    def _extract_qa_pairs_cached(self, conversation_history: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
        """
        Extract question-answer pairs from conversation history with caching.
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            List of (question, answer) tuples
        """
        # Check cache first
        cache_key = self._get_conversation_cache_key(conversation_history)
        now = datetime.utcnow()
        
        if (cache_key in self._qa_pairs_cache and 
            cache_key in self._qa_pairs_cache_timestamps and
            (now - self._qa_pairs_cache_timestamps[cache_key]).total_seconds() < CACHE_TTL):
            return self._qa_pairs_cache[cache_key]
        
        # Cache miss - extract Q&A pairs
        qa_pairs = self._extract_qa_pairs(conversation_history)
        
        # Cache the result
        self._qa_pairs_cache[cache_key] = qa_pairs
        self._qa_pairs_cache_timestamps[cache_key] = now
        
        return qa_pairs
    
    def _extract_qa_pairs(self, conversation_history: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
        """
        Extract question-answer pairs from conversation history.
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            List of (question, answer) tuples
        """
        qa_pairs = []
        
        # Optimization: Pre-classify messages by role and order for faster matching
        interviewer_indices = []
        user_indices = []
        
        for i, msg in enumerate(conversation_history):
            role = msg.get("role")
            if role == "assistant" and "interviewer" in msg.get("agent", ""):
                interviewer_indices.append(i)
            elif role == "user":
                user_indices.append(i)
        
        # Match questions with answers
        for interviewer_idx in interviewer_indices:
            question_msg = conversation_history[interviewer_idx]
            question = question_msg.get("content", "")
            
            # Find the next user message after this interviewer message
            next_user_idx = None
            for user_idx in user_indices:
                if user_idx > interviewer_idx:
                    next_user_idx = user_idx
                    break
            
            if next_user_idx is not None:
                answer_msg = conversation_history[next_user_idx]
                answer = answer_msg.get("content", "")
                
                # Only add if both question and answer exist
                if question and answer:
                    qa_pairs.append((question, answer))
        
        return qa_pairs
    
    def _get_conversation_cache_key(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Generate a cache key for a conversation history.
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            Cache key string
        """
        if not conversation_history:
            return "empty"
        
        # Use the length and last message ID as a simple cache key
        last_msg = conversation_history[-1]
        msg_count = len(conversation_history)
        
        # Try to get unique identifiers from the history
        last_timestamp = last_msg.get("timestamp", "")
        last_content = last_msg.get("content", "")
        content_hash = str(hash(last_content) % 10000)  # Last 4 digits of hash
        
        return f"msgs_{msg_count}_last_{content_hash}_{last_timestamp[-8:]}"
    
    def _clear_cache(self, session_id: Optional[str] = None) -> None:
        """
        Clear the service caches.
        
        Args:
            session_id: Optional session ID to clear specific cache entries
        """
        if session_id:
            # Clear specific cache entries (not implemented yet)
            pass
        else:
            # Clear all caches
            self._metrics_cache = {}
            self._metrics_cache_timestamps = {}
            self._qa_pairs_cache = {}
            self._qa_pairs_cache_timestamps = {}
    
    def _handle_interview_end(self, event: Event) -> None:
        """
        Handle interview end events to archive the session.
        
        Args:
            event: The interview end event
        """
        session_id = event.data.get("session_id")
        self.logger.info(f"Received interview_end event for session {session_id}")
        
        # Clear caches for this session
        self._clear_cache(session_id)
    
    def _handle_user_response(self, event: Event) -> None:
        """
        Handle user response events for metrics tracking.
        
        Args:
            event: The user response event
        """
        # Clear caches since conversation has changed
        session_id = event.data.get("session_id")
        if session_id:
            self._clear_cache(session_id)
    
    def _handle_agent_response(self, event: Event) -> None:
        """
        Handle agent response events for metrics tracking.
        
        Args:
            event: The agent response event
        """
        # Clear caches since conversation has changed
        session_id = event.data.get("session_id")
        if session_id:
            self._clear_cache(session_id) 