"""
Phase III: Authentication & User Management Tests
Tests Supabase authentication integration and user session management.
"""

import os
import sys
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

# Add backend to Python path
sys.path.insert(0, 'backend')

# Set environment variables
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret"
os.environ["GOOGLE_API_KEY"] = "test-api-key"
os.environ["ASSEMBLYAI_API_KEY"] = "test-assemblyai-key"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test-aws-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test-aws-secret"
os.environ["DEEPGRAM_API_KEY"] = "test-deepgram-key"

# Import app after setting environment variables
from backend.main import app
from backend.database.db_manager import DatabaseManager
from backend.api.auth_api import create_auth_api, get_current_user

# Using a different approach for tests, avoid the problematic TestClient
def test_environment_setup():
    """Test that environment variables are set correctly."""
    assert os.environ.get("SUPABASE_URL") == "https://test.supabase.co"
    assert os.environ.get("SUPABASE_SERVICE_KEY") == "test-key"
    assert os.environ.get("SUPABASE_JWT_SECRET") == "test-jwt-secret"
    assert os.environ.get("GOOGLE_API_KEY") == "test-api-key"


class TestAuthAPI:
    """Test the authentication API endpoints."""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        with patch('backend.database.db_manager.create_client') as mock_create_client:
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            
            # Setup auth methods
            mock_client.auth = MagicMock()
            
            # Return the mock client
            yield mock_client
    
    @pytest.fixture
    def mock_database_manager(self, mock_supabase):
        """Mock DatabaseManager with test data."""
        return DatabaseManager()
    
    @pytest.mark.asyncio
    async def test_register_user(self, mock_database_manager):
        """Test user registration."""
        # Mock the register_user method
        mock_database_manager.register_user = AsyncMock()
        mock_database_manager.register_user.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'user': {
                'id': 'test-user-id',
                'email': 'test@example.com',
                'created_at': '2023-01-01T00:00:00Z'
            }
        }
        
        # Create a test app
        test_app = FastAPI()
        
        # Mock get_database_manager dependency - corrected to return the instance directly
        with patch('backend.api.auth_api.get_database_manager', return_value=mock_database_manager):
            create_auth_api(test_app)
        
        # Create a test client directly inline rather than at module level
        client = TestClient(test_app)
        
        # Test registration
        response = client.post('/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Assert response
        assert response.status_code == 200
        assert 'access_token' in response.json()
        assert 'refresh_token' in response.json()
        assert 'user' in response.json()
        assert response.json()['user']['email'] == 'test@example.com'
        
        # Assert method called
        mock_database_manager.register_user.assert_called_once_with(
            email='test@example.com',
            password='password123'
        )
    
    @pytest.mark.asyncio
    async def test_login_user(self, mock_database_manager):
        """Test user login."""
        # Mock the login_user method
        mock_database_manager.login_user = AsyncMock()
        mock_database_manager.login_user.return_value = {
            'access_token': 'test-access-token',
            'refresh_token': 'test-refresh-token',
            'user': {
                'id': 'test-user-id',
                'email': 'test@example.com',
                'created_at': '2023-01-01T00:00:00Z'
            }
        }
        
        # Create a test app
        test_app = FastAPI()
        
        # Mock get_database_manager dependency
        async def mock_get_db():
            return mock_database_manager
        
        # Create auth API with mocked dependency
        with patch('backend.api.auth_api.get_database_manager', return_value=mock_get_db()):
            create_auth_api(test_app)
        
        # Test login
        test_client = TestClient(test_app)
        response = test_client.post('/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Assert response
        assert response.status_code == 200
        assert 'access_token' in response.json()
        assert 'refresh_token' in response.json()
        assert 'user' in response.json()
        assert response.json()['user']['email'] == 'test@example.com'
        
        # Assert method called
        mock_database_manager.login_user.assert_called_once_with(
            email='test@example.com',
            password='password123'
        )
    
    @pytest.mark.asyncio
    async def test_get_current_user(self, mock_database_manager):
        """Test the get_current_user dependency."""
        # Mock JWT decode
        with patch('jwt.decode') as mock_decode:
            # Setup mock return value
            mock_decode.return_value = {
                'sub': 'test-user-id',
                'exp': 2000000000  # Far in the future
            }
            
            # Mock get_user method
            mock_database_manager.get_user = AsyncMock()
            mock_database_manager.get_user.return_value = {
                'id': 'test-user-id',
                'email': 'test@example.com',
                'created_at': '2023-01-01T00:00:00Z'
            }
            
            # Create mock credentials
            mock_credentials = MagicMock()
            mock_credentials.credentials = 'test-token'
            
            # Call the function
            user = await get_current_user(mock_credentials, mock_database_manager)
            
            # Assert result
            assert user['id'] == 'test-user-id'
            assert user['email'] == 'test@example.com'
            
            # Assert mock called
            mock_database_manager.get_user.assert_called_once_with('test-user-id')
    
    @pytest.mark.asyncio
    async def test_protected_endpoint(self, mock_database_manager):
        """Test a protected endpoint."""
        # Mock the get_user method
        mock_database_manager.get_user = AsyncMock()
        mock_database_manager.get_user.return_value = {
            'id': 'test-user-id',
            'email': 'test@example.com',
            'created_at': '2023-01-01T00:00:00Z'
        }
        
        # Create a test app
        test_app = FastAPI()
        
        # Mock get_database_manager dependency
        async def mock_get_db():
            return mock_database_manager
        
        # Create a protected endpoint
        from fastapi import Depends
        from backend.api.auth_api import get_current_user
        
        @test_app.get('/protected')
        async def protected_endpoint(current_user: dict = Depends(get_current_user)):
            return {'message': 'Access granted', 'user': current_user}
        
        # Mock JWT verification
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {
                'sub': 'test-user-id',
                'exp': 2000000000  # Far in the future
            }
            
            # Test endpoint with token
            test_client = TestClient(test_app)
            response = test_client.get('/protected', headers={
                'Authorization': 'Bearer test-token'
            })
            
            # Assert response
            assert response.status_code == 200
            assert response.json()['message'] == 'Access granted'
            assert response.json()['user']['id'] == 'test-user-id'


class TestProtectedAgentAPI:
    """Test the protected agent API endpoints."""
    
    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        with patch('backend.database.db_manager.create_client') as mock_create_client:
            mock_client = MagicMock()
            mock_create_client.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def mock_auth(self):
        """Mock auth dependency."""
        with patch('backend.api.agent_api.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = {
                'id': 'test-user-id',
                'email': 'test@example.com',
                'created_at': '2023-01-01T00:00:00Z'
            }
            yield mock_get_current_user
    
    @pytest.fixture
    def mock_session_registry(self):
        """Mock ThreadSafeSessionRegistry."""
        with patch('backend.api.agent_api.get_session_registry') as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.create_new_session = AsyncMock()
            mock_registry.create_new_session.return_value = 'test-session-id'
            
            mock_get_registry.return_value = mock_registry
            yield mock_registry
    
    @pytest.mark.asyncio
    async def test_create_session_with_auth(self, mock_auth, mock_session_registry, mock_supabase):
        """Test creating a session with authentication."""
        from backend.api.agent_api import create_agent_api
        
        # Create a test app
        test_app = FastAPI()
        create_agent_api(test_app)
        
        # Test endpoint
        test_client = TestClient(test_app)
        response = test_client.post('/interview/session', json={
            'job_role': 'Software Engineer',
            'job_description': 'Test job description',
            'style': 'formal'
        })
        
        # Assert response
        assert response.status_code == 200
        assert response.json()['session_id'] == 'test-session-id'
        
        # Assert method called with user ID
        mock_session_registry.create_new_session.assert_called_once()
        args, kwargs = mock_session_registry.create_new_session.call_args
        assert kwargs['user_id'] == 'test-user-id'


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 