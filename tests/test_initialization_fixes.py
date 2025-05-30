"""
Test suite for initialization fixes.
Tests ThreadSafeSessionRegistry dependency injection and database operations.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

# Set test environment variables before imports
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-key"
os.environ["GOOGLE_API_KEY"] = "test-api-key"

from backend.services import initialize_services, get_session_registry, ServiceRegistry
from backend.services.session_manager import ThreadSafeSessionRegistry
from backend.database.db_manager import DatabaseManager
from backend.services.llm_service import LLMService
from backend.utils.event_bus import EventBus
from backend.agents.config_models import SessionConfig


class TestThreadSafeSessionRegistryInitialization:
    """Test ThreadSafeSessionRegistry initialization with dependencies."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch('backend.database.db_manager.create_client') as mock_supabase, \
             patch('backend.services.llm_service.ChatGoogleGenerativeAI') as mock_llm:
            
            # Setup mock Supabase
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            # Setup mock LLM
            mock_llm_instance = Mock()
            mock_llm.return_value = mock_llm_instance
            
            yield {
                'supabase': mock_client,
                'llm': mock_llm_instance
            }
    
    def test_service_registry_session_registry_creation(self, mock_dependencies):
        """Test that ServiceRegistry creates ThreadSafeSessionRegistry with correct dependencies."""
        registry = ServiceRegistry()
        
        # Get session registry - this should trigger creation with dependencies
        session_registry = registry.get_session_registry()
        
        # Verify it's a ThreadSafeSessionRegistry instance
        assert isinstance(session_registry, ThreadSafeSessionRegistry)
        
        # Verify it has the required dependencies
        assert hasattr(session_registry, 'db_manager')
        assert hasattr(session_registry, 'llm_service')
        assert hasattr(session_registry, 'event_bus')
        
        # Verify dependencies are the correct types
        assert isinstance(session_registry.db_manager, DatabaseManager)
        assert isinstance(session_registry.llm_service, LLMService)
        assert isinstance(session_registry.event_bus, EventBus)
    
    def test_initialize_services_creates_session_registry_with_dependencies(self, mock_dependencies):
        """Test that initialize_services creates ThreadSafeSessionRegistry with dependencies."""
        # Reset any existing global state
        import backend.services
        backend.services._session_registry = None
        backend.services._database_manager = None
        
        # Initialize services
        initialize_services()
        
        # Get the session registry
        session_registry = get_session_registry()
        
        # Verify it's properly initialized
        assert isinstance(session_registry, ThreadSafeSessionRegistry)
        assert hasattr(session_registry, 'db_manager')
        assert hasattr(session_registry, 'llm_service')
        assert hasattr(session_registry, 'event_bus')


class TestSessionRegistryFunctionality:
    """Test ThreadSafeSessionRegistry functionality with mocked database."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        mock = AsyncMock()
        mock.create_session.return_value = "test-session-id"
        mock.load_session_state.return_value = {
            "session_id": "test-session-id",
            "session_config": {"job_role": "Software Engineer"},
            "conversation_history": [],
            "per_turn_feedback_log": [],
            "session_stats": {}
        }
        mock.save_session_state.return_value = True
        return mock
    
    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service."""
        with patch('backend.services.llm_service.ChatGoogleGenerativeAI'):
            return LLMService()
    
    @pytest.fixture
    def session_registry(self, mock_db_manager, mock_llm_service):
        """Create session registry with mocked dependencies."""
        event_bus = EventBus()
        return ThreadSafeSessionRegistry(
            db_manager=mock_db_manager,
            llm_service=mock_llm_service,
            event_bus=event_bus
        )
    
    @pytest.mark.asyncio
    async def test_create_new_session(self, session_registry, mock_db_manager):
        """Test creating a new session."""
        config = SessionConfig(job_role="Software Engineer")
        session_id = await session_registry.create_new_session(
            user_id="test-user",
            initial_config=config
        )
        
        assert session_id == "test-session-id"
        mock_db_manager.create_session.assert_called_once()
        
        # Verify config was converted to dict
        call_args = mock_db_manager.create_session.call_args
        assert call_args[1]["user_id"] == "test-user"
        assert call_args[1]["initial_config"]["job_role"] == "Software Engineer"
    
    @pytest.mark.asyncio
    async def test_get_session_manager(self, session_registry, mock_db_manager):
        """Test getting session manager loads from database."""
        with patch('backend.agents.orchestrator.AgentSessionManager.from_session_data') as mock_from_data:
            mock_manager = Mock()
            mock_manager.session_id = "test-session-id"
            mock_from_data.return_value = mock_manager
            
            manager = await session_registry.get_session_manager("test-session-id")
            
            assert manager == mock_manager
            mock_db_manager.load_session_state.assert_called_with("test-session-id")
            mock_from_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_session_access(self, session_registry, mock_db_manager):
        """Test that concurrent access to same session returns same manager."""
        with patch('backend.agents.orchestrator.AgentSessionManager.from_session_data') as mock_from_data:
            mock_manager = Mock()
            mock_manager.session_id = "test-session-id"
            mock_from_data.return_value = mock_manager
            
            # Simulate concurrent access
            tasks = [
                session_registry.get_session_manager("test-session-id")
                for _ in range(5)
            ]
            
            managers = await asyncio.gather(*tasks)
            
            # Should return the same manager instance for all requests
            assert all(manager == mock_manager for manager in managers)
            # Database should only be called once due to session locking
            assert mock_db_manager.load_session_state.call_count == 1
    
    @pytest.mark.asyncio
    async def test_save_session(self, session_registry, mock_db_manager):
        """Test saving an active session."""
        # First get a session manager to make it active
        with patch('backend.agents.orchestrator.AgentSessionManager.from_session_data') as mock_from_data:
            mock_manager = Mock()
            mock_manager.session_id = "test-session-id"
            mock_manager.to_dict.return_value = {"session_id": "test-session-id", "data": "test"}
            mock_from_data.return_value = mock_manager
            
            # Get the manager (makes it active)
            await session_registry.get_session_manager("test-session-id")
            
            # Save the session
            success = await session_registry.save_session("test-session-id")
            
            assert success is True
            mock_db_manager.save_session_state.assert_called_once()


class TestDatabaseManagerInitialization:
    """Test DatabaseManager initialization and environment variable handling."""
    
    def test_database_manager_requires_environment_variables(self):
        """Test that DatabaseManager raises ValueError without required env vars."""
        # Temporarily remove env vars
        original_url = os.environ.get("SUPABASE_URL")
        original_key = os.environ.get("SUPABASE_SERVICE_KEY")
        
        try:
            if "SUPABASE_URL" in os.environ:
                del os.environ["SUPABASE_URL"]
            if "SUPABASE_SERVICE_KEY" in os.environ:
                del os.environ["SUPABASE_SERVICE_KEY"]
            
            with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_SERVICE_KEY must be set"):
                DatabaseManager()
        
        finally:
            # Restore env vars
            if original_url:
                os.environ["SUPABASE_URL"] = original_url
            if original_key:
                os.environ["SUPABASE_SERVICE_KEY"] = original_key
    
    def test_database_manager_with_environment_variables(self):
        """Test that DatabaseManager initializes correctly with env vars."""
        with patch('backend.database.db_manager.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            
            db_manager = DatabaseManager()
            
            assert db_manager.url == "https://test.supabase.co"
            assert db_manager.key == "test-key"
            assert db_manager.supabase == mock_client
            mock_create.assert_called_once_with("https://test.supabase.co", "test-key")


class TestAuthenticationFlow:
    """Test authentication flow with proper error handling."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager for auth tests."""
        mock = AsyncMock()
        return mock
    
    @pytest.mark.asyncio
    async def test_user_registration_success(self, mock_db_manager):
        """Test successful user registration."""
        # Mock successful Supabase auth response
        mock_auth_response = Mock()
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_session = Mock()
        mock_session.access_token = "token-123"
        mock_session.refresh_token = "refresh-123"
        
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session
        
        with patch('backend.database.db_manager.create_client') as mock_create:
            mock_client = Mock()
            mock_client.auth.sign_up.return_value = mock_auth_response
            mock_client.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_create.return_value = mock_client
            
            db_manager = DatabaseManager()
            result = await db_manager.register_user("test@example.com", "password123")
            
            assert result["access_token"] == "token-123"
            assert result["refresh_token"] == "refresh-123"
            assert result["user"]["id"] == "user-123"
            assert result["user"]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_user_login_success(self, mock_db_manager):
        """Test successful user login."""
        # Mock successful Supabase auth response
        mock_auth_response = Mock()
        mock_user = Mock()
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_user.created_at = "2023-01-01T00:00:00Z"
        mock_session = Mock()
        mock_session.access_token = "token-123"
        mock_session.refresh_token = "refresh-123"
        
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session
        
        with patch('backend.database.db_manager.create_client') as mock_create:
            mock_client = Mock()
            mock_client.auth.sign_in_with_password.return_value = mock_auth_response
            mock_create.return_value = mock_client
            
            db_manager = DatabaseManager()
            result = await db_manager.login_user("test@example.com", "password123")
            
            assert result["access_token"] == "token-123"
            assert result["refresh_token"] == "refresh-123"
            assert result["user"]["id"] == "user-123"
            assert result["user"]["email"] == "test@example.com"


class TestIntegrationWithMockAuth:
    """Test integration with mock authentication for development."""
    
    def test_mock_auth_initialization(self):
        """Test that mock auth can be enabled via environment variable."""
        with patch.dict(os.environ, {"USE_MOCK_AUTH": "true"}):
            # Reset global state
            import backend.services
            backend.services._database_manager = None
            backend.services._session_registry = None
            
            with patch('backend.database.mock_db_manager.MockDatabaseManager') as mock_class:
                mock_instance = Mock()
                mock_class.return_value = mock_instance
                
                initialize_services()
                
                # Verify mock database manager was used
                mock_class.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 