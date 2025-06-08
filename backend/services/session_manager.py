"""
Thread-safe session management for concurrent user support.
Manages session-specific AgentSessionManager instances with database persistence.
"""

import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from backend.database.db_manager import DatabaseManager
from backend.services.llm_service import LLMService
from backend.utils.event_bus import EventBus
from backend.agents.config_models import SessionConfig
from backend.agents.orchestrator import AgentSessionManager
from backend.config import get_logger

logger = get_logger(__name__)


class ThreadSafeSessionRegistry:
    """
    Thread-safe registry for managing session-specific AgentSessionManager instances.
    Handles loading/saving session state from database and manages active sessions in memory.
    """
    
    def __init__(self, db_manager: DatabaseManager, llm_service: LLMService, event_bus: EventBus):
        """
        Initialize the session registry.
        
        Args:
            db_manager: Database manager for persistence
            llm_service: LLM service for agent initialization
            event_bus: Event bus for inter-component communication
        """
        self.db_manager = db_manager
        self.llm_service = llm_service
        self.event_bus = event_bus
        self._active_sessions: Dict[str, AgentSessionManager] = {}
        self._session_locks: Dict[str, asyncio.Lock] = {}
        self._session_access_times: Dict[str, datetime] = {}  # Track last access time
        self._registry_lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        logger.info("ThreadSafeSessionRegistry initialized")

    async def start_cleanup_task(self, cleanup_interval_minutes: int = 30, max_idle_minutes: int = 60) -> None:
        """
        Start background task to cleanup inactive sessions.
        
        Args:
            cleanup_interval_minutes: How often to run cleanup (default: 30 minutes)
            max_idle_minutes: Max idle time before session cleanup (default: 60 minutes)
        """
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(
                self._periodic_cleanup(cleanup_interval_minutes, max_idle_minutes)
            )
            logger.info(f"Started session cleanup task (interval: {cleanup_interval_minutes}min, max_idle: {max_idle_minutes}min)")

    async def _periodic_cleanup(self, cleanup_interval_minutes: int, max_idle_minutes: int) -> None:
        """
        Periodically cleanup inactive sessions.
        
        Args:
            cleanup_interval_minutes: How often to run cleanup
            max_idle_minutes: Max idle time before session cleanup
        """
        while True:
            try:
                await asyncio.sleep(cleanup_interval_minutes * 60)  # Convert to seconds
                cleaned_count = await self.cleanup_inactive_sessions(max_idle_minutes)
                if cleaned_count > 0:
                    logger.info(f"Periodic cleanup: released {cleaned_count} inactive sessions")
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")
                break
            except Exception as e:
                logger.exception(f"Error in periodic session cleanup: {e}")

    async def get_session_manager(self, session_id: str) -> AgentSessionManager:
        """
        Get or create session manager for specific session.
        Loads from database if not in memory.
        
        Args:
            session_id: The session ID to get manager for
            
        Returns:
            AgentSessionManager: Session-specific manager instance
        """
        # Import here to avoid circular dependency
        from backend.agents.orchestrator import AgentSessionManager
        
        # Ensure we have a lock for this session
        async with self._registry_lock:
            if session_id not in self._session_locks:
                self._session_locks[session_id] = asyncio.Lock()
        
        # Use session-specific lock
        async with self._session_locks[session_id]:
            if session_id not in self._active_sessions:
                # Load from database and create manager
                session_data = await self.db_manager.load_session_state(session_id)
                
                if session_data:
                    manager = AgentSessionManager.from_session_data(
                        session_data=session_data,
                        llm_service=self.llm_service,
                        event_bus=self.event_bus,
                        logger=logger.getChild(f"Session-{session_id[:8]}")
                    )
                else:
                    # Session doesn't exist - this should not happen in normal flow
                    # but we handle it gracefully
                    logger.warning(f"Session {session_id} not found in database")
                    raise ValueError(f"Session {session_id} not found")
                
                self._active_sessions[session_id] = manager
                logger.info(f"Loaded session manager for: {session_id}")
            
            # Update access time
            self._session_access_times[session_id] = datetime.utcnow()
            
            return self._active_sessions[session_id]

    async def create_new_session(self, user_id: Optional[str] = None, 
                               initial_config: Optional[SessionConfig] = None) -> str:
        """
        Create a new session with default configuration.
        
        Args:
            user_id: Optional user ID to associate with session
            initial_config: Optional initial session configuration
            
        Returns:
            str: The created session ID
        """
        # Convert SessionConfig to dict if provided
        config_dict = None
        if initial_config:
            # FIXED: Manually convert enums to strings since Pydantic v2 model_dump(mode='json') doesn't work properly for enums
            config_dict = initial_config.model_dump() if hasattr(initial_config, 'model_dump') else vars(initial_config)
            
            # Manually convert enum values to strings for JSON serialization
            for key, value in config_dict.items():
                if hasattr(value, 'value'):  # This is an enum
                    config_dict[key] = value.value
        
        # Create session in database
        session_id = await self.db_manager.create_session(
            user_id=user_id,
            initial_config=config_dict
        )
        
        logger.info(f"Created new session: {session_id}")
        return session_id

    async def save_session(self, session_id: str) -> bool:
        """
        Save session state to database with enhanced error handling.
        
        Args:
            session_id: The session ID to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        if session_id in self._active_sessions:
            try:
                manager = self._active_sessions[session_id]
                state_data = manager.to_dict()
                
                # Log session data size for monitoring
                conversation_count = len(state_data.get("conversation_history", []))
                feedback_count = len(state_data.get("per_turn_feedback_log", []))
                logger.debug(f"Saving session {session_id}: {conversation_count} messages, {feedback_count} feedback items")
                
                success = await self.db_manager.save_session_state(session_id, state_data)
                
                if success:
                    logger.debug(f"Successfully saved session {session_id} to database")
                else:
                    logger.error(f"Database save failed for session {session_id}")
                
                return success
                
            except Exception as e:
                logger.exception(f"Error saving session {session_id}: {e}")
                return False
        else:
            logger.warning(f"Attempted to save inactive session: {session_id}")
            return False

    async def release_session(self, session_id: str) -> bool:
        """
        Save and release session manager from memory.
        
        Args:
            session_id: The session ID to release
            
        Returns:
            bool: True if successful, False otherwise
        """
        async with self._registry_lock:
            if session_id in self._active_sessions:
                # Save to database first
                success = await self.save_session(session_id)
                
                if success:
                    # FIXED: Comprehensive cleanup to prevent memory leaks
                    del self._active_sessions[session_id]
                    if session_id in self._session_locks:
                        del self._session_locks[session_id]
                    if session_id in self._session_access_times:
                        del self._session_access_times[session_id]
                    logger.info(f"Released session: {session_id}")
                    return True
                else:
                    logger.error(f"Failed to save session before release: {session_id}")
                    return False
            else:
                # FIXED: Even if session not active, clean up any lingering references
                if session_id in self._session_locks:
                    del self._session_locks[session_id]
                    logger.debug(f"Cleaned up orphaned session lock: {session_id}")
                if session_id in self._session_access_times:
                    del self._session_access_times[session_id]
                    logger.debug(f"Cleaned up orphaned access time: {session_id}")
                logger.warning(f"Attempted to release inactive session: {session_id}")
                return True  # Consider it successful if already released

    async def get_active_session_count(self) -> int:
        """
        Get the number of currently active sessions in memory.
        
        Returns:
            int: Number of active sessions
        """
        return len(self._active_sessions)

    async def cleanup_inactive_sessions(self, max_idle_minutes: int = 60) -> int:
        """
        Clean up sessions that have been idle for too long.
        
        Args:
            max_idle_minutes: Maximum idle time before cleanup
            
        Returns:
            int: Number of sessions cleaned up
        """
        cleaned_count = 0
        current_time = datetime.utcnow()
        max_idle_delta = timedelta(minutes=max_idle_minutes)
        
        # FIXED: Get session candidates quickly under lock to avoid deadlock
        session_candidates = []
        async with self._registry_lock:
            # Quickly build list of candidates without long operations under lock
            for session_id, last_access in self._session_access_times.items():
                if session_id in self._active_sessions and last_access:
                    session_candidates.append((session_id, last_access))
        
        # FIXED: Process candidates outside lock to prevent deadlock
        sessions_to_release = []
        for session_id, last_access in session_candidates:
            if (current_time - last_access) > max_idle_delta:
                sessions_to_release.append(session_id)
        
        # Release sessions outside any locks to avoid deadlock
        for session_id in sessions_to_release:
            try:
                success = await self.release_session(session_id)
                if success:
                    cleaned_count += 1
                    logger.debug(f"Released idle session: {session_id}")
            except Exception as e:
                logger.exception(f"Error releasing idle session {session_id}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} idle sessions (idle > {max_idle_minutes} minutes)")
        
        return cleaned_count 

    async def get_memory_usage_stats(self) -> Dict[str, int]:
        """
        Get memory usage statistics.
        
        Returns:
            Dict with memory usage stats
        """
        current_time = datetime.utcnow()
        
        # Calculate session age distribution
        session_ages = []
        for session_id in self._active_sessions:
            last_access = self._session_access_times.get(session_id, current_time)
            age_minutes = (current_time - last_access).total_seconds() / 60
            session_ages.append(age_minutes)
        
        stats = {
            "active_sessions": len(self._active_sessions),
            "tracked_locks": len(self._session_locks),
            "tracked_access_times": len(self._session_access_times),
            "avg_age_minutes": sum(session_ages) / len(session_ages) if session_ages else 0,
            "max_age_minutes": max(session_ages) if session_ages else 0
        }
        
        return stats

    async def stop_cleanup_task(self) -> None:
        """Stop the background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Session cleanup task stopped")

    def _cleanup_session_references(self, session_id: str) -> None:
        """
        FIXED: Helper method to clean up all session references to prevent memory leaks.
        Should be called whenever a session fails to initialize or needs cleanup.
        
        Args:
            session_id: The session ID to clean up
        """
        if session_id in self._session_locks:
            del self._session_locks[session_id]
            logger.debug(f"Cleaned up session lock for: {session_id}")
        if session_id in self._session_access_times:
            del self._session_access_times[session_id]
            logger.debug(f"Cleaned up access time for: {session_id}")
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            logger.debug(f"Cleaned up active session for: {session_id}") 