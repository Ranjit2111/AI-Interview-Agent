"""
Session manager service for interview sessions.
Provides functionality for creating, retrieving, and managing sessions.
"""

import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Type
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError

from backend.models.interview import InterviewSession, InterviewStyle, SessionMode
from backend.utils.event_bus import Event, EventBus

# Define a cache TTL (time to live) in seconds
CACHE_TTL = 60  # 1 minute cache expiration

class SessionManager:
    """
    Service for managing interview sessions, including creation, retrieval, and persistence.
    """
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the session manager.
        
        Args:
            event_bus: Event bus for publishing session events
            logger: Logger instance
        """
        self.active_sessions = {}
        self.session_metadata = {}
        self.event_bus = event_bus or EventBus()
        self.logger = logger or logging.getLogger(__name__)
        
        # Add caching dictionaries
        self._session_info_cache = {}  # Cache for session info
        self._session_info_cache_timestamps = {}  # Cache timestamps
        self._sessions_list_cache = {}  # Cache for list_sessions results
        self._sessions_list_cache_timestamp = None  # Cache timestamp for list_sessions
        
        # Subscribe to events
        if self.event_bus:
            self.event_bus.subscribe("interview_start", self._handle_interview_start)
            self.event_bus.subscribe("interview_end", self._handle_interview_end)
            self.event_bus.subscribe("session_reset", self._handle_session_reset)
    
    def create_session(
        self,
        mode: str,
        job_role: str,
        job_description: str,
        interview_style: Union[InterviewStyle, str],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new interview session.
        
        Args:
            mode: Orchestrator mode
            job_role: Job role for the interview
            job_description: Job description
            interview_style: Interview style
            user_id: Optional user identifier
            
        Returns:
            Dictionary with session information
        """
        try:
            from backend.agents import AgentOrchestrator
        except ImportError:
            self.logger.error("Failed to import AgentOrchestrator")
            raise ImportError("AgentOrchestrator not found")
        
        # Convert string interview style to enum if needed
        if isinstance(interview_style, str):
            try:
                interview_style = InterviewStyle[interview_style]
            except KeyError:
                self.logger.warning(f"Invalid interview style: {interview_style}, using FORMAL")
                interview_style = InterviewStyle.FORMAL
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(
            event_bus=self.event_bus,
            logger=self.logger
        )
        
        # Store session
        self.active_sessions[session_id] = orchestrator
        
        # Store metadata
        timestamp = datetime.utcnow().isoformat()
        self.session_metadata[session_id] = {
            "session_id": session_id,
            "job_role": job_role,
            "job_description": job_description, 
            "interview_style": interview_style.name,
            "mode": mode,
            "user_id": user_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "active": True
        }
        
        # Initialize session
        orchestrator.initialize_session(
            InterviewSession(
                id=session_id,
                user_id=user_id,
                job_role=job_role,
                job_description=job_description,
                style=interview_style,
                mode=SessionMode.INTERVIEW  # Default mode
            )
        )
        
        # Clear any cached data since we've added a new session
        self._clear_session_list_cache()
        
        # Return session info
        return self.session_metadata[session_id]
    
    def get_session(self, session_id: str) -> Optional["AgentOrchestrator"]:
        """
        Get the orchestrator for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Orchestrator instance or None if session not found
        """
        return self.active_sessions.get(session_id)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information dictionary or None if session not found
        """
        # Check cache first
        now = datetime.utcnow()
        cache_key = session_id
        
        if (cache_key in self._session_info_cache and 
            cache_key in self._session_info_cache_timestamps and
            (now - self._session_info_cache_timestamps[cache_key]).total_seconds() < CACHE_TTL):
            return self._session_info_cache[cache_key]
        
        # Cache miss - fetch information
        info = self.session_metadata.get(session_id)
        
        # Update cache
        if info:
            self._session_info_cache[cache_key] = info
            self._session_info_cache_timestamps[cache_key] = now
        
        return info
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all active sessions or sessions for a specific user.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            List of session information dictionaries
        """
        # Check cache first
        now = datetime.utcnow()
        cache_key = f"user_{user_id}" if user_id else "all"
        
        if (cache_key in self._sessions_list_cache and 
            self._sessions_list_cache_timestamp and
            (now - self._sessions_list_cache_timestamp).total_seconds() < CACHE_TTL):
            return self._sessions_list_cache[cache_key]
        
        # Cache miss - fetch sessions
        if user_id:
            sessions = [
                info for info in self.session_metadata.values()
                if info.get("user_id") == user_id
            ]
        else:
            sessions = list(self.session_metadata.values())
        
        # Update cache
        self._sessions_list_cache[cache_key] = sessions
        self._sessions_list_cache_timestamp = now
        
        return sessions
    
    def end_session(self, session_id: str) -> bool:
        """
        End an active session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was found and ended, False otherwise
        """
        orchestrator = self.active_sessions.get(session_id)
        if not orchestrator:
            return False
        
        # Publish event to notify components
        self.event_bus.publish(Event(
            event_type="interview_end",
            source="session_manager",
            data={
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        # Keep metadata for historical reference
        # but mark as inactive
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["active"] = False
            self.session_metadata[session_id]["ended_at"] = datetime.utcnow().isoformat()
        
        # Clear caches
        self._clear_caches_for_session(session_id)
        self._clear_session_list_cache()
        
        return True
    
    def persist_session(self, db: DBSession, session_id: str) -> bool:
        """
        Persist session data to the database.
        
        Args:
            db: Database session
            session_id: Session identifier
            
        Returns:
            True if persistence was successful, False otherwise
        """
        orchestrator = self.active_sessions.get(session_id)
        if not orchestrator:
            self.logger.warning(f"Session {session_id} not found for persistence")
            return False
        
        metadata = self.session_metadata.get(session_id, {})
        user_id = metadata.get("user_id") or orchestrator.user_id
        
        # Only persist if we have a user ID
        if not user_id:
            self.logger.info(f"Session {session_id} has no user ID, skipping persistence")
            return False
        
        try:
            # Check if session already exists - use a single query with first() to limit DB round-trips
            existing = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
            
            if existing:
                # Update existing session
                existing.updated_at = datetime.utcnow()
                db.commit()
                self.logger.info(f"Updated existing session {session_id} in database")
            else:
                # Create new session record
                style = orchestrator.interview_style
                session = InterviewSession(
                    id=session_id,
                    user_id=user_id,
                    job_role=orchestrator.job_role,
                    job_description=orchestrator.job_description,
                    style=style,
                    created_at=datetime.fromisoformat(metadata.get("created_at", datetime.utcnow().isoformat())),
                    updated_at=datetime.utcnow()
                )
                db.add(session)
                db.commit()
                self.logger.info(f"Persisted session {session_id} to database")
            
            # Update cache
            self._clear_caches_for_session(session_id)
            
            return True
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error persisting session {session_id}: {str(e)}")
            return False
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """
        Remove inactive sessions older than the specified age.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of sessions removed
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        # Find sessions older than cutoff time - optimize this loop
        for session_id, metadata in self.session_metadata.items():
            # Only consider inactive sessions that are not in active_sessions
            if session_id not in self.active_sessions:
                try:
                    # Parse timestamp only once and store result
                    created_at_str = metadata.get("created_at", "")
                    if created_at_str:
                        created_at = datetime.fromisoformat(created_at_str)
                        if created_at < cutoff_time:
                            sessions_to_remove.append(session_id)
                except (ValueError, TypeError):
                    # If we can't parse the timestamp, assume it's old
                    sessions_to_remove.append(session_id)
        
        # Remove sessions
        for session_id in sessions_to_remove:
            self.session_metadata.pop(session_id, None)
            self._clear_caches_for_session(session_id)
        
        # Clear list cache if we removed any sessions
        if sessions_to_remove:
            self._clear_session_list_cache()
        
        self.logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions")
        return len(sessions_to_remove)
    
    def _clear_caches_for_session(self, session_id: str) -> None:
        """
        Clear all caches related to a specific session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._session_info_cache:
            del self._session_info_cache[session_id]
            
        if session_id in self._session_info_cache_timestamps:
            del self._session_info_cache_timestamps[session_id]
    
    def _clear_session_list_cache(self) -> None:
        """Clear the sessions list cache."""
        self._sessions_list_cache = {}
        self._sessions_list_cache_timestamp = None
    
    def _handle_interview_start(self, event: Event) -> None:
        """
        Handle interview start events.
        
        Args:
            event: The interview start event
        """
        session_id = event.data.get("session_id")
        if not session_id:
            return
        
        # Update session metadata if exists
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["active"] = True
            self.session_metadata[session_id]["updated_at"] = datetime.utcnow().isoformat()
            
            # Clear caches
            self._clear_caches_for_session(session_id)
            self._clear_session_list_cache()
    
    def _handle_interview_end(self, event: Event) -> None:
        """
        Handle interview end events.
        
        Args:
            event: The interview end event
        """
        session_id = event.data.get("session_id")
        if not session_id:
            return
        
        # Update session metadata if exists
        if session_id in self.session_metadata:
            self.session_metadata[session_id]["active"] = False
            self.session_metadata[session_id]["ended_at"] = datetime.utcnow().isoformat()
            self.session_metadata[session_id]["updated_at"] = datetime.utcnow().isoformat()
            
            # Clear caches
            self._clear_caches_for_session(session_id)
            self._clear_session_list_cache()
    
    def _handle_session_reset(self, event: Event) -> None:
        """
        Handle session reset events.
        
        Args:
            event: The session reset event
        """
        session_id = event.data.get("session_id")
        if not session_id or session_id not in self.session_metadata:
            return
        
        # Update session metadata
        self.session_metadata[session_id]["reset_at"] = datetime.utcnow().isoformat()
        self.session_metadata[session_id]["updated_at"] = datetime.utcnow().isoformat()
        
        # Clear caches
        self._clear_caches_for_session(session_id)
        self._clear_session_list_cache() 