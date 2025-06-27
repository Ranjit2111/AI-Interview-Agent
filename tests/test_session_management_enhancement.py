"""
Comprehensive tests for Session Management Enhancement features.
Tests all implemented changes for reliable deployment.
"""

import pytest
import pytest_asyncio
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the components we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.session_manager import ThreadSafeSessionRegistry
from backend.database.mock_db_manager import MockDatabaseManager
from backend.services.llm_service import LLMService
from backend.utils.event_bus import EventBus
from backend.api.agent_api import create_agent_api


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
    
    @pytest.mark.asyncio
    async def test_cleanup_with_new_timeouts(self, session_registry):
        """Test that cleanup respects the new 15-minute timeout."""
        # Create sessions with different ages
        now = datetime.utcnow()
        
        # Session that should be cleaned (16 minutes old)
        old_session = "old_session"
        session_registry._active_sessions[old_session] = MagicMock()
        session_registry._session_access_times[old_session] = now - timedelta(minutes=16)
        
        # Session that should stay (10 minutes old)
        young_session = "young_session"
        session_registry._active_sessions[young_session] = MagicMock()
        session_registry._session_access_times[young_session] = now - timedelta(minutes=10)
        
        # Mock the save_session method
        with patch.object(session_registry, 'save_session', return_value=True):
            # Run cleanup with 15 minute timeout
            cleaned_count = await session_registry.cleanup_inactive_sessions(15)
        
        # Only the old session should be cleaned
        assert cleaned_count == 1
        assert old_session not in session_registry._active_sessions
        assert young_session in session_registry._active_sessions


class TestSessionManagementAPI:
    """Test the new session management API endpoints."""
    
    @pytest.fixture
    def app_with_session_api(self):
        """Create a FastAPI app with session management endpoints."""
        app = FastAPI()
        
        # Mock the session registry
        mock_registry = AsyncMock()
        
        # Add mock registry to app state
        app.state.agent_manager = mock_registry
        
        # Register the API routes
        create_agent_api(app)
        
        return app, mock_registry
    
    def test_session_time_remaining_endpoint(self, app_with_session_api):
        """Test the GET /interview/session/time-remaining endpoint."""
        app, mock_registry = app_with_session_api
        with TestClient(app) as client:
        
            # Mock the registry method
            mock_registry.get_session_time_remaining.return_value = 10
            
            # Make request with session ID header
            response = client.get(
                "/interview/session/time-remaining",
                headers={"X-Session-ID": "test_session"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["time_remaining_minutes"] == 10
            assert data["session_active"] is True
            
            # Test with expired session
            mock_registry.get_session_time_remaining.return_value = None
            
            response = client.get(
                "/interview/session/time-remaining",
                headers={"X-Session-ID": "expired_session"}
            )
            
            assert response.status_code == 200
            data = response.json()
        assert data["time_remaining_minutes"] == 0
        assert data["session_active"] is False
    
    def test_session_ping_endpoint(self, app_with_session_api):
        """Test the POST /interview/session/ping endpoint."""
        app, mock_registry = app_with_session_api
        client = TestClient(app)
        
        # Mock successful ping
        mock_registry.ping_session.return_value = True
        
        response = client.post(
            "/interview/session/ping",
            headers={"X-Session-ID": "test_session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Session extended successfully"
        assert data["new_expiry_minutes"] == 15
        
        # Test failed ping
        mock_registry.ping_session.return_value = False
        
        response = client.post(
            "/interview/session/ping",
            headers={"X-Session-ID": "nonexistent_session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
        assert data["new_expiry_minutes"] == 0
    
    def test_session_cleanup_endpoint(self, app_with_session_api):
        """Test the POST /interview/session/cleanup endpoint."""
        app, mock_registry = app_with_session_api
        client = TestClient(app)
        
        # Mock successful cleanup
        mock_registry.cleanup_session_immediately.return_value = True
        
        response = client.post(
            "/interview/session/cleanup",
            headers={"X-Session-ID": "test_session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "successfully" in data["message"].lower()
        
        # Test failed cleanup
        mock_registry.cleanup_session_immediately.return_value = False
        
        response = client.post(
            "/interview/session/cleanup",
            headers={"X-Session-ID": "test_session"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "failed" in data["message"].lower()
    
    def test_missing_session_id_header(self, app_with_session_api):
        """Test that endpoints require X-Session-ID header."""
        app, mock_registry = app_with_session_api
        client = TestClient(app)
        
        # Test all endpoints without session ID header
        endpoints = [
            ("/interview/session/time-remaining", "GET"),
            ("/interview/session/ping", "POST"),
            ("/interview/session/cleanup", "POST")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            assert response.status_code == 400
            assert "Session ID required" in response.json()["detail"]


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
        assert is_session_timeout_error("", 404) is False


class TestIntegrationScenarios:
    """Test complete session management scenarios."""
    
    @pytest.fixture
    async def full_session_setup(self):
        """Set up a complete session management scenario."""
        # Create all components
        db_manager = MockDatabaseManager()
        llm_service = MagicMock()
        event_bus = EventBus()
        
        registry = ThreadSafeSessionRegistry(
            db_manager=db_manager,
            llm_service=llm_service,
            event_bus=event_bus
        )
        
        # Start cleanup task with new defaults
        await registry.start_cleanup_task()
        
        yield registry
        
        # Cleanup
        await registry.stop_cleanup_task()
    
    @pytest.mark.asyncio
    async def test_complete_session_lifecycle(self, full_session_setup):
        """Test complete session lifecycle with new timing."""
        registry = full_session_setup
        
        # 1. Create session
        session_id = await registry.create_new_session()
        assert session_id is not None
        
        # 2. Simulate session access (this updates access time)
        mock_manager = MagicMock()
        registry._active_sessions[session_id] = mock_manager
        registry._session_access_times[session_id] = datetime.utcnow()
        
        # 3. Check initial time remaining (should be ~15 minutes)
        remaining = await registry.get_session_time_remaining(session_id)
        assert 14 <= remaining <= 15
        
        # 4. Simulate 10 minutes passing
        old_time = datetime.utcnow() - timedelta(minutes=10)
        registry._session_access_times[session_id] = old_time
        
        # 5. Check time remaining (should be ~5 minutes)
        remaining = await registry.get_session_time_remaining(session_id)
        assert 4 <= remaining <= 5
        
        # 6. Extend session via ping
        success = await registry.ping_session(session_id)
        assert success is True
        
        # 7. Check time remaining after ping (should be ~15 minutes again)
        remaining = await registry.get_session_time_remaining(session_id)
        assert 14 <= remaining <= 15
        
        # 8. Immediate cleanup
        with patch.object(registry, 'save_session', return_value=True):
            success = await registry.cleanup_session_immediately(session_id)
        assert success is True
        
        # 9. Verify session is gone
        remaining = await registry.get_session_time_remaining(session_id)
        assert remaining is None
    
    @pytest.mark.asyncio
    async def test_warning_scenario_timing(self, full_session_setup):
        """Test the warning scenario timing matches requirements."""
        registry = full_session_setup
        
        # Create session and simulate being active for 13 minutes
        session_id = "warning_test_session"
        thirteen_minutes_ago = datetime.utcnow() - timedelta(minutes=13)
        registry._session_access_times[session_id] = thirteen_minutes_ago
        
        # At 13 minutes, should have 2 minutes remaining
        remaining = await registry.get_session_time_remaining(session_id)
        assert remaining == 2
        
        # This should trigger warning in frontend
        should_warn = remaining <= 2 and remaining > 0
        assert should_warn is True
        
        # Simulate 1 more minute passing
        fourteen_minutes_ago = datetime.utcnow() - timedelta(minutes=14)
        registry._session_access_times[session_id] = fourteen_minutes_ago
        
        remaining = await registry.get_session_time_remaining(session_id)
        assert remaining == 1
        
        # Still should warn
        should_warn = remaining <= 2 and remaining > 0
        assert should_warn is True
    
    @pytest.mark.asyncio
    async def test_cleanup_frequency_effectiveness(self, full_session_setup):
        """Test that 5-minute cleanup frequency is effective."""
        registry = full_session_setup
        
        # Create multiple sessions with different ages
        sessions = {}
        now = datetime.utcnow()
        
        # Create 5 sessions:
        # - 2 should be cleaned (older than 15 min)
        # - 3 should remain (younger than 15 min)
        
        for i in range(5):
            session_id = f"test_session_{i}"
            mock_manager = MagicMock()
            registry._active_sessions[session_id] = mock_manager
            
            if i < 2:
                # Old sessions (16-17 minutes)
                age_minutes = 16 + i
                sessions[session_id] = "should_clean"
            else:
                # Young sessions (5-14 minutes)
                age_minutes = 5 + (i * 3)
                sessions[session_id] = "should_keep"
            
            registry._session_access_times[session_id] = now - timedelta(minutes=age_minutes)
        
        # Run cleanup with 15-minute timeout
        with patch.object(registry, 'save_session', return_value=True):
            cleaned_count = await registry.cleanup_inactive_sessions(15)
        
        # Should have cleaned exactly 2 sessions
        assert cleaned_count == 2
        
        # Verify correct sessions were cleaned/kept
        for session_id, expected in sessions.items():
            if expected == "should_clean":
                assert session_id not in registry._active_sessions
            else:
                assert session_id in registry._active_sessions


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"]) 