"""
Session management service for interview sessions.
Provides functionality for tracking and managing active sessions.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from sqlalchemy.orm import Session as DBSession

from backend.agents import AgentOrchestrator
from backend.utils.event_bus import EventBus, Event
from backend.models.interview import InterviewSession, InterviewStyle


class SessionManager:
    """
    Service for managing interview sessions, providing persistence and retrieval.
    """
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the session manager service.
        
        Args:
            event_bus: Event bus for publishing/subscribing to session events
            logger: Logger instance
        """
        self.event_bus = event_bus or EventBus()
        self.logger = logger or logging.getLogger(__name__)
        
        # In-memory storage for active sessions
        self.active_sessions: Dict[str, AgentOrchestrator] = {}
        
        # Session metadata for quick access
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Subscribe to relevant events
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
            job_role: Target job role
            job_description: Job description
            interview_style: Interview style
            user_id: Optional user identifier
            
        Returns:
            Session information dictionary
        """
        # Convert string style to enum if needed
        if isinstance(interview_style, str):
            try:
                style = InterviewStyle(interview_style.upper())
            except ValueError:
                style = InterviewStyle.FORMAL
        else:
            style = interview_style
        
        # Create a session ID
        session_id = str(uuid.uuid4())
        
        # Create an orchestrator instance
        orchestrator = AgentOrchestrator(
            mode=mode,
            job_role=job_role,
            job_description=job_description,
            interview_style=style,
            event_bus=self.event_bus
        )
        
        # Set the session ID and user ID
        orchestrator.session_id = session_id
        orchestrator.user_id = user_id
        
        # Store in active sessions
        self.active_sessions[session_id] = orchestrator
        
        # Store metadata
        created_at = datetime.utcnow()
        self.session_metadata[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "job_role": job_role,
            "interview_style": style.value,
            "mode": mode,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
            "active_agent": orchestrator.active_agent_id
        }
        
        # Return session info
        return {
            "session_id": session_id,
            "job_role": job_role,
            "interview_style": style.value,
            "mode": mode,
            "created_at": created_at.isoformat(),
            "active_agent": orchestrator.active_agent_id
        }
    
    def get_session(self, session_id: str) -> Optional[AgentOrchestrator]:
        """
        Get an active session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Orchestrator instance or None if not found
        """
        return self.active_sessions.get(session_id)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session information or None if not found
        """
        return self.session_metadata.get(session_id)
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List active sessions, optionally filtered by user ID.
        
        Args:
            user_id: Optional user identifier to filter by
            
        Returns:
            List of session information dictionaries
        """
        if user_id:
            return [
                info for info in self.session_metadata.values()
                if info.get("user_id") == user_id
            ]
        else:
            return list(self.session_metadata.values())
    
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
            # Check if session already exists
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
        
        # Find sessions older than cutoff time
        for session_id, metadata in self.session_metadata.items():
            if session_id not in self.active_sessions:  # Only consider inactive sessions
                try:
                    created_at = datetime.fromisoformat(metadata.get("created_at", ""))
                    if created_at < cutoff_time:
                        sessions_to_remove.append(session_id)
                except (ValueError, TypeError):
                    # If we can't parse the timestamp, assume it's old
                    sessions_to_remove.append(session_id)
        
        # Remove sessions
        for session_id in sessions_to_remove:
            self.session_metadata.pop(session_id, None)
        
        self.logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions")
        return len(sessions_to_remove)
    
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