"""
Thread-safe session management for concurrent user support.
Manages session-specific AgentSessionManager instances with database persistence.
"""

import asyncio
import logging
from typing import Dict, Optional
from backend.database.db_manager import DatabaseManager
from backend.agents.orchestrator import AgentSessionManager
from backend.services.llm_service import LLMService
from backend.utils.event_bus import EventBus
from backend.agents.config_models import SessionConfig
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
        self._registry_lock = asyncio.Lock()
        logger.info("ThreadSafeSessionRegistry initialized")

    async def get_session_manager(self, session_id: str) -> AgentSessionManager:
        """
        Get or create session manager for specific session.
        Loads from database if not in memory.
        
        Args:
            session_id: The session ID to get manager for
            
        Returns:
            AgentSessionManager: Session-specific manager instance
        """
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
            config_dict = initial_config.dict() if hasattr(initial_config, 'dict') else vars(initial_config)
        
        # Create session in database
        session_id = await self.db_manager.create_session(
            user_id=user_id,
            initial_config=config_dict
        )
        
        logger.info(f"Created new session: {session_id}")
        return session_id

    async def save_session(self, session_id: str) -> bool:
        """
        Save session state to database.
        
        Args:
            session_id: The session ID to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        if session_id in self._active_sessions:
            manager = self._active_sessions[session_id]
            state_data = manager.to_dict()
            return await self.db_manager.save_session_state(session_id, state_data)
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
                    # Remove from memory
                    del self._active_sessions[session_id]
                    if session_id in self._session_locks:
                        del self._session_locks[session_id]
                    logger.info(f"Released session: {session_id}")
                    return True
                else:
                    logger.error(f"Failed to save session before release: {session_id}")
                    return False
            else:
                logger.warning(f"Attempted to release inactive session: {session_id}")
                return True  # Consider it successful if already released

    async def get_active_session_count(self) -> int:
        """
        Get the number of currently active sessions in memory.
        
        Returns:
            int: Number of active sessions
        """
        return len(self._active_sessions)

    async def cleanup_inactive_sessions(self, max_idle_minutes: int = 30) -> int:
        """
        Clean up sessions that have been idle for too long.
        
        Args:
            max_idle_minutes: Maximum idle time before cleanup
            
        Returns:
            int: Number of sessions cleaned up
        """
        # For now, we'll implement a simple cleanup that saves all active sessions
        # In the future, this could check last activity time
        cleaned_count = 0
        
        async with self._registry_lock:
            sessions_to_release = list(self._active_sessions.keys())
        
        for session_id in sessions_to_release:
            # Save but don't release - just ensure data is persisted
            await self.save_session(session_id)
            cleaned_count += 1
        
        logger.info(f"Saved {cleaned_count} active sessions during cleanup")
        return cleaned_count 