"""
Test suite for Phase I: Core Architecture Refactoring
Tests database operations, session management, and API endpoints.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

# Set test environment variables before imports
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test-key"
os.environ["GOOGLE_API_KEY"] = "test-api-key"

from backend.database.db_manager import DatabaseManager
from backend.services.session_manager import ThreadSafeSessionRegistry
from backend.agents.orchestrator import AgentSessionManager
from backend.agents.config_models import SessionConfig
from backend.services.llm_service import LLMService
from backend.utils.event_bus import EventBus


class TestDatabaseManager:
    """Test database manager functionality."""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        with patch('backend.database.db_manager.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def db_manager(self, mock_supabase):
        """Create database manager with mocked Supabase."""
        return DatabaseManager()
    
    @pytest.mark.asyncio
    async def test_create_session(self, db_manager, mock_supabase):
        """Test session creation."""
        # Mock successful response
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"session_id": "test-session-id"}
        ]
        
        session_id = await db_manager.create_session(
            user_id="test-user",
            initial_config={"job_role": "Software Engineer"}
        )
        
        assert session_id == "test-session-id"
        mock_supabase.table.assert_called_with("interview_sessions")
    
    @pytest.mark.asyncio
    async def test_load_session_state(self, db_manager, mock_supabase):
        """Test loading session state."""
        # Mock response data
        mock_data = {
            "session_id": "test-session-id",
            "session_config": {"job_role": "Software Engineer"},
            "conversation_history": [],
            "per_turn_feedback_log": [],
            "session_stats": {}
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_data]
        
        result = await db_manager.load_session_state("test-session-id")
        
        assert result is not None
        assert result["session_id"] == "test-session-id"
        assert result["session_config"]["job_role"] == "Software Engineer"
    
    @pytest.mark.asyncio
    async def test_save_session_state(self, db_manager, mock_supabase):
        """Test saving session state."""
        # Mock successful update
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"updated": True}]
        
        state_data = {
            "session_config": {"job_role": "Software Engineer"},
            "conversation_history": [{"role": "user", "content": "Hello"}],
            "per_turn_feedback_log": [],
            "session_stats": {"total_messages": 1}
        }
        
        success = await db_manager.save_session_state("test-session-id", state_data)
        
        assert success is True
        mock_supabase.table.assert_called_with("interview_sessions")
    
    @pytest.mark.asyncio
    async def test_create_speech_task(self, db_manager, mock_supabase):
        """Test speech task creation."""
        # Mock successful response
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"task_id": "test-task-id"}
        ]
        
        task_id = await db_manager.create_speech_task("test-session-id", "stt_batch")
        
        assert task_id == "test-task-id"
        mock_supabase.table.assert_called_with("speech_tasks")


class TestThreadSafeSessionRegistry:
    """Test session registry functionality."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        mock = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service."""
        return Mock(spec=LLMService)
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus."""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def session_registry(self, mock_db_manager, mock_llm_service, mock_event_bus):
        """Create session registry with mocked dependencies."""
        return ThreadSafeSessionRegistry(
            db_manager=mock_db_manager,
            llm_service=mock_llm_service,
            event_bus=mock_event_bus
        )
    
    @pytest.mark.asyncio
    async def test_create_new_session(self, session_registry, mock_db_manager):
        """Test creating a new session."""
        # Mock database response
        mock_db_manager.create_session.return_value = "new-session-id"
        
        config = SessionConfig(job_role="Software Engineer")
        session_id = await session_registry.create_new_session(
            user_id="test-user",
            initial_config=config
        )
        
        assert session_id == "new-session-id"
        mock_db_manager.create_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_manager(self, session_registry, mock_db_manager):
        """Test getting session manager."""
        # Mock database response
        mock_session_data = {
            "session_id": "test-session-id",
            "session_config": {"job_role": "Software Engineer"},
            "conversation_history": [],
            "per_turn_feedback_log": [],
            "session_stats": {}
        }
        mock_db_manager.load_session_state.return_value = mock_session_data
        
        with patch.object(AgentSessionManager, 'from_session_data') as mock_from_data:
            mock_manager = Mock()
            mock_from_data.return_value = mock_manager
            
            manager = await session_registry.get_session_manager("test-session-id")
            
            assert manager == mock_manager
            mock_db_manager.load_session_state.assert_called_with("test-session-id")
    
    @pytest.mark.asyncio
    async def test_concurrent_session_access(self, session_registry, mock_db_manager):
        """Test concurrent access to the same session."""
        # Mock database response
        mock_session_data = {
            "session_id": "test-session-id",
            "session_config": {"job_role": "Software Engineer"},
            "conversation_history": [],
            "per_turn_feedback_log": [],
            "session_stats": {}
        }
        mock_db_manager.load_session_state.return_value = mock_session_data
        
        with patch.object(AgentSessionManager, 'from_session_data') as mock_from_data:
            mock_manager = Mock()
            mock_from_data.return_value = mock_manager
            
            # Simulate concurrent access
            tasks = [
                session_registry.get_session_manager("test-session-id")
                for _ in range(5)
            ]
            
            managers = await asyncio.gather(*tasks)
            
            # Should return the same manager instance for all requests
            assert all(manager == mock_manager for manager in managers)
            # Database should only be called once
            assert mock_db_manager.load_session_state.call_count == 1


class TestAgentSessionManager:
    """Test session manager functionality."""
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service."""
        return Mock(spec=LLMService)
    
    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus."""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def session_config(self):
        """Create test session config."""
        return SessionConfig(job_role="Software Engineer")
    
    @pytest.fixture
    def session_manager(self, mock_llm_service, mock_event_bus, session_config):
        """Create session manager."""
        with patch('backend.config.get_logger') as mock_logger:
            mock_logger.return_value = Mock()
            return AgentSessionManager(
                llm_service=mock_llm_service,
                event_bus=mock_event_bus,
                logger=mock_logger.return_value,
                session_config=session_config,
                session_id="test-session-id"
            )
    
    def test_session_initialization(self, session_manager):
        """Test session manager initialization."""
        assert session_manager.session_id == "test-session-id"
        assert session_manager.session_config.job_role == "Software Engineer"
        assert session_manager.conversation_history == []
    
    def test_to_dict_serialization(self, session_manager):
        """Test session state serialization."""
        # Add some data
        session_manager.conversation_history.append({"role": "user", "content": "Hello"})
        session_manager.api_call_count = 1
        
        state_dict = session_manager.to_dict()
        
        assert state_dict["session_id"] == "test-session-id"
        assert len(state_dict["conversation_history"]) == 1
        assert state_dict["session_stats"]["total_api_calls"] == 1
    
    def test_from_session_data(self, mock_llm_service, mock_event_bus):
        """Test creating manager from session data."""
        session_data = {
            "session_id": "restored-session-id",
            "session_config": {"job_role": "Data Scientist"},
            "conversation_history": [{"role": "user", "content": "Test"}],
            "per_turn_feedback_log": [],
            "session_stats": {"total_api_calls": 2}
        }
        
        with patch('backend.config.get_logger') as mock_logger:
            mock_logger.return_value = Mock()
            
            manager = AgentSessionManager.from_session_data(
                session_data=session_data,
                llm_service=mock_llm_service,
                event_bus=mock_event_bus,
                logger=mock_logger.return_value
            )
            
            assert manager.session_id == "restored-session-id"
            assert manager.session_config.job_role == "Data Scientist"
            assert len(manager.conversation_history) == 1
            assert manager.api_call_count == 2
    
    def test_get_langchain_config(self, session_manager):
        """Test LangChain configuration generation."""
        config = session_manager.get_langchain_config()
        
        assert config == {"configurable": {"thread_id": "test-session-id"}}


class TestAPIIntegration:
    """Test API integration with session management."""
    
    @pytest.mark.asyncio
    async def test_session_id_dependency(self):
        """Test session ID extraction from headers."""
        from backend.api.agent_api import get_session_id
        
        # Test with valid session ID
        session_id = await get_session_id("test-session-id")
        assert session_id == "test-session-id"
        
        # Test with no session ID should raise exception
        with pytest.raises(Exception):
            await get_session_id(None)


@pytest.mark.asyncio
async def test_end_to_end_session_flow():
    """Test complete session flow from creation to usage."""
    
    # Mock all external dependencies
    with patch('backend.database.db_manager.create_client') as mock_create_client, \
         patch('backend.config.get_logger') as mock_logger:
        
        # Setup mocks
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        mock_logger.return_value = Mock()
        
        # Mock database responses
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"session_id": "test-session-id"}
        ]
        
        mock_session_data = {
            "session_id": "test-session-id",
            "session_config": {"job_role": "Software Engineer"},
            "conversation_history": [],
            "per_turn_feedback_log": [],
            "session_stats": {}
        }
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_session_data]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"updated": True}]
        
        # Create components
        db_manager = DatabaseManager()
        llm_service = Mock(spec=LLMService)
        event_bus = Mock(spec=EventBus)
        session_registry = ThreadSafeSessionRegistry(db_manager, llm_service, event_bus)
        
        # Test flow
        # 1. Create session
        config = SessionConfig(job_role="Software Engineer")
        session_id = await session_registry.create_new_session(initial_config=config)
        assert session_id == "test-session-id"
        
        # 2. Get session manager
        manager = await session_registry.get_session_manager(session_id)
        assert manager.session_id == session_id
        
        # 3. Save session
        success = await session_registry.save_session(session_id)
        assert success is True


def test_environment_setup():
    """Test that environment variables are properly set for testing."""
    assert os.environ.get("SUPABASE_URL") == "https://test.supabase.co"
    assert os.environ.get("SUPABASE_SERVICE_KEY") == "test-key"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 