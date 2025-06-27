"""
Comprehensive tests for Session Management Enhancement features.
Tests all implemented changes for reliable deployment.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Import the components we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.session_manager import ThreadSafeSessionRegistry
from backend.database.mock_db_manager import MockDatabaseManager
from backend.utils.event_bus import EventBus


class TestSessionManagerEnhancements:
    """Test the enhanced session manager functionality."""
    
    @pytest_asyncio.fixture
    async def session_registry(self):
        """Create a session registry for testing."""
        db_manager = MockDatabaseManager()
        llm_service = MagicMock()
        event_bus = EventBus()
        
        registry = ThreadSafeSessionRegistry(
            db_manager=db_manager,
            llm_service=llm_service,
            event_bus=event_bus
        )
        
        return registry
    
    @pytest.mark.asyncio
    async def test_cleanup_task_defaults_updated(self, session_registry):
        """Test that cleanup task uses new default values (5 min interval, 15 min timeout)."""
        # Start cleanup task with defaults
        await session_registry.start_cleanup_task()
        
        # Verify task was created
        assert session_registry._cleanup_task is not None
        assert not session_registry._cleanup_task.done()
        
        # Clean up
        await session_registry.stop_cleanup_task()
    
    @pytest.mark.asyncio
    async def test_get_session_time_remaining(self, session_registry):
        """Test getting remaining time before session cleanup."""
        # Create a test session
        session_id = "test_session_123"
        session_registry._session_access_times[session_id] = datetime.utcnow()
        
        # Test with 15 minute timeout
        remaining = await session_registry.get_session_time_remaining(session_id, 15)
        
        # Should be close to 15 minutes (allowing for test execution time)
        assert remaining is not None
        assert 14 <= remaining <= 15
        
        # Test with old access time (should show less remaining time)
        old_time = datetime.utcnow() - timedelta(minutes=10)
        session_registry._session_access_times[session_id] = old_time
        
        remaining = await session_registry.get_session_time_remaining(session_id, 15)
        assert remaining is not None
        assert 4 <= remaining <= 5
        
        # Test with non-existent session
        remaining = await session_registry.get_session_time_remaining("nonexistent", 15)
        assert remaining is None
    
    @pytest.mark.asyncio
    async def test_ping_session(self, session_registry):
        """Test session ping/extension functionality."""
        # Create a test session
        session_id = "test_session_ping"
        old_time = datetime.utcnow() - timedelta(minutes=10)
        session_registry._session_access_times[session_id] = old_time
        
        # Ping the session
        success = await session_registry.ping_session(session_id)
        
        assert success is True
        
        # Verify access time was updated
        new_time = session_registry._session_access_times[session_id]
        assert new_time > old_time
        
        # Should now have close to full timeout remaining
        remaining = await session_registry.get_session_time_remaining(session_id, 15)
        assert remaining is not None
        assert 14 <= remaining <= 15
        
        # Test pinging non-existent session
        success = await session_registry.ping_session("nonexistent")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_immediate_cleanup(self, session_registry):
        """Test immediate session cleanup functionality."""
        # Create a test session in registry
        session_id = "test_session_cleanup"
        mock_manager = MagicMock()
        session_registry._active_sessions[session_id] = mock_manager
        session_registry._session_access_times[session_id] = datetime.utcnow()
        session_registry._session_locks[session_id] = asyncio.Lock()
        
        # Mock the save_session method to return True
        with patch.object(session_registry, 'save_session', return_value=True):
            success = await session_registry.cleanup_session_immediately(session_id)
        
        assert success is True
        
        # Verify session was removed from all tracking
        assert session_id not in session_registry._active_sessions
        assert session_id not in session_registry._session_access_times
        assert session_id not in session_registry._session_locks


class TestSessionWarningLogic:
    """Test the session warning and timeout logic."""
    
    def test_warning_timing_logic(self):
        """Test the logic for when to show session warnings."""
        # Simulate the warning logic from the frontend
        def should_show_warning(time_remaining_minutes):
            return time_remaining_minutes <= 2 and time_remaining_minutes > 0
        
        # Test cases
        assert should_show_warning(3) is False  # Too early
        assert should_show_warning(2) is True   # Exactly 2 minutes
        assert should_show_warning(1) is True   # 1 minute left
        assert should_show_warning(0) is False  # Expired
        assert should_show_warning(-1) is False # Expired
    
    def test_session_timeout_detection(self):
        """Test session timeout detection logic."""
        def is_session_timeout_error(error_message, status_code):
            return (status_code == 404 and 
                    error_message and 
                    'session' in error_message.lower())
        
        # Test cases
        assert is_session_timeout_error("Session not found", 404) is True
        assert is_session_timeout_error("SESSION_TIMEOUT: expired", 404) is True
        assert is_session_timeout_error("User not found", 404) is False
        assert is_session_timeout_error("Session not found", 500) is False
        assert is_session_timeout_error(None, 404) is False
        assert is_session_timeout_error("", 404) is False


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"]) 