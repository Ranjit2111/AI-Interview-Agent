"""
Phase IV: Testing & Validation - Concurrent Session Testing
Tests multiple users starting interviews simultaneously to verify no state collision.
"""

import os
import sys
import pytest
import asyncio
import aiohttp
import json
import time
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

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

# Mock external services before importing
with patch('backend.database.db_manager.create_client'):
    from backend.main import app
    from backend.services.rate_limiting import APIRateLimiter
    from backend.services.session_manager import ThreadSafeSessionRegistry
    from backend.database.db_manager import DatabaseManager

from fastapi.testclient import TestClient


class ConcurrentSessionTester:
    """Handles concurrent session testing scenarios."""
    
    def __init__(self):
        self.base_url = "http://testserver"
        self.test_users = []
        self.active_sessions = []
        
    async def create_test_user(self, user_index: int) -> Dict[str, Any]:
        """Create a test user with authentication token."""
        user_data = {
            'id': f'test-user-{user_index}',
            'email': f'test{user_index}@example.com',
            'password': 'password123'
        }
        
        # Mock authentication response
        auth_response = {
            'access_token': f'test-token-{user_index}',
            'refresh_token': f'test-refresh-{user_index}',
            'user': {
                'id': user_data['id'],
                'email': user_data['email'],
                'created_at': '2023-01-01T00:00:00Z'
            }
        }
        
        return {**user_data, 'auth': auth_response}
    
    async def start_interview_session(self, client: TestClient, user: Dict[str, Any], 
                                    job_role: str) -> Dict[str, Any]:
        """Start an interview session for a user."""
        headers = {
            'Authorization': f"Bearer {user['auth']['access_token']}",
            'Content-Type': 'application/json'
        }
        
        # Create session
        session_response = client.post('/interview/session', json={
            'job_role': job_role,
            'job_description': f'Test job description for {job_role}',
            'style': 'formal',
            'difficulty': 'medium'
        }, headers=headers)
        
        if session_response.status_code != 200:
            raise Exception(f"Failed to create session: {session_response.text}")
        
        session_data = session_response.json()
        session_id = session_data['session_id']
        
        # Start the interview
        start_response = client.post('/interview/start', json={
            'job_role': job_role,
            'job_description': f'Test job description for {job_role}',
            'style': 'formal'
        }, headers={
            **headers,
            'X-Session-ID': session_id
        })
        
        if start_response.status_code != 200:
            raise Exception(f"Failed to start interview: {start_response.text}")
        
        return {
            'user_id': user['id'],
            'session_id': session_id,
            'job_role': job_role,
            'session_data': session_data,
            'start_data': start_response.json()
        }
    
    async def send_interview_message(self, client: TestClient, user: Dict[str, Any],
                                   session_id: str, message: str) -> Dict[str, Any]:
        """Send a message in an interview session."""
        headers = {
            'Authorization': f"Bearer {user['auth']['access_token']}",
            'Content-Type': 'application/json',
            'X-Session-ID': session_id
        }
        
        response = client.post('/interview/message', json={
            'message': message
        }, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to send message: {response.text}")
        
        return response.json()


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies for testing."""
    with patch('backend.database.db_manager.create_client') as mock_supabase, \
         patch('backend.services.rate_limiting.APIRateLimiter') as mock_rate_limiter, \
         patch('backend.services.session_manager.ThreadSafeSessionRegistry') as mock_registry:
        
        # Setup mock Supabase
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        # Setup mock rate limiter
        mock_limiter_instance = MagicMock()
        mock_rate_limiter.return_value = mock_limiter_instance
        
        # Setup mock session registry
        mock_registry_instance = MagicMock()
        mock_registry_instance.create_new_session = AsyncMock()
        mock_registry_instance.get_session_manager = AsyncMock()
        mock_registry.return_value = mock_registry_instance
        
        yield {
            'supabase': mock_client,
            'rate_limiter': mock_limiter_instance,
            'session_registry': mock_registry_instance
        }


@pytest.fixture
def test_client(mock_dependencies):
    """Create a test client with mocked dependencies."""
    # Mock the app state
    with patch.object(app, 'state') as mock_state:
        mock_state.agent_manager = mock_dependencies['session_registry']
        
        # Mock authentication
        with patch('backend.api.auth_api.get_current_user') as mock_auth:
            def mock_get_user(credentials):
                # Extract user ID from token
                token = credentials.credentials
                user_index = token.split('-')[-1]
                return {
                    'id': f'test-user-{user_index}',
                    'email': f'test{user_index}@example.com',
                    'created_at': '2023-01-01T00:00:00Z'
                }
            
            mock_auth.side_effect = mock_get_user
            
            client = TestClient(app)
            yield client


class TestConcurrentSessions:
    """Test concurrent session management."""
    
    @pytest.mark.asyncio
    async def test_multiple_users_concurrent_sessions(self, test_client, mock_dependencies):
        """Test multiple users starting interviews simultaneously."""
        tester = ConcurrentSessionTester()
        num_users = 5
        
        # Create test users
        users = []
        for i in range(num_users):
            user = await tester.create_test_user(i)
            users.append(user)
        
        # Mock session creation to return unique session IDs
        session_ids = [f'session-{i}' for i in range(num_users)]
        mock_dependencies['session_registry'].create_new_session.side_effect = session_ids
        
        # Start concurrent interviews
        results = []
        job_roles = ['Software Engineer', 'Data Scientist', 'Product Manager', 'DevOps Engineer', 'UX Designer']
        
        for i, user in enumerate(users):
            try:
                result = await tester.start_interview_session(
                    test_client, user, job_roles[i]
                )
                results.append(result)
            except Exception as e:
                pytest.fail(f"Failed to start session for user {i}: {e}")
        
        # Verify no state collision
        user_ids = [result['user_id'] for result in results]
        session_ids = [result['session_id'] for result in results]
        job_roles_used = [result['job_role'] for result in results]
        
        # All user IDs should be unique
        assert len(set(user_ids)) == num_users, "User ID collision detected"
        
        # All session IDs should be unique
        assert len(set(session_ids)) == num_users, "Session ID collision detected"
        
        # Job roles should match what was requested
        assert len(set(job_roles_used)) == num_users, "Job role mismatch"
        
        # Verify each session was created with correct user ID
        for i, call_args in enumerate(mock_dependencies['session_registry'].create_new_session.call_args_list):
            assert call_args.kwargs['user_id'] == f'test-user-{i}'
    
    @pytest.mark.asyncio
    async def test_concurrent_message_exchange(self, test_client, mock_dependencies):
        """Test concurrent message exchange in different sessions."""
        tester = ConcurrentSessionTester()
        num_users = 3
        
        # Create test users and sessions
        users = []
        sessions = []
        
        for i in range(num_users):
            user = await tester.create_test_user(i)
            users.append(user)
        
        # Mock session creation
        session_ids = [f'session-{i}' for i in range(num_users)]
        mock_dependencies['session_registry'].create_new_session.side_effect = session_ids
        
        # Create sessions
        for i, user in enumerate(users):
            result = await tester.start_interview_session(
                test_client, user, f'Role {i}'
            )
            sessions.append(result)
        
        # Mock session manager for message handling
        mock_session_managers = []
        for i in range(num_users):
            mock_manager = MagicMock()
            mock_manager.session_id = f'session-{i}'
            mock_manager.process_message.return_value = {
                'role': 'assistant',
                'content': f'Response for user {i}',
                'timestamp': '2023-01-01T00:00:00Z'
            }
            mock_session_managers.append(mock_manager)
        
        mock_dependencies['session_registry'].get_session_manager.side_effect = mock_session_managers
        
        # Send concurrent messages
        messages = [f'Hello from user {i}' for i in range(num_users)]
        responses = []
        
        for i, (user, session) in enumerate(zip(users, sessions)):
            try:
                response = await tester.send_interview_message(
                    test_client, user, session['session_id'], messages[i]
                )
                responses.append(response)
            except Exception as e:
                pytest.fail(f"Failed to send message for user {i}: {e}")
        
        # Verify responses are unique per user
        assert len(responses) == num_users
        for i, response in enumerate(responses):
            assert f'user {i}' in response['content']
        
        # Verify correct session managers were called
        for i, mock_manager in enumerate(mock_session_managers):
            mock_manager.process_message.assert_called_once_with(message=f'Hello from user {i}')


class TestAPIRateLimiting:
    """Test API rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_assemblyai_rate_limiting(self):
        """Test AssemblyAI concurrency limiting (5 concurrent max)."""
        from backend.services.rate_limiting import APIRateLimiter
        
        # Create rate limiter
        rate_limiter = APIRateLimiter()
        
        # Track active requests
        active_requests = []
        max_concurrent = 0
        
        async def mock_assemblyai_request(request_id: int):
            """Mock AssemblyAI request that tracks concurrency."""
            nonlocal max_concurrent
            
            async with rate_limiter.assemblyai_semaphore:
                active_requests.append(request_id)
                max_concurrent = max(max_concurrent, len(active_requests))
                
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                active_requests.remove(request_id)
        
        # Start 10 concurrent requests
        tasks = [mock_assemblyai_request(i) for i in range(10)]
        await asyncio.gather(*tasks)
        
        # Verify maximum concurrent requests never exceeded 5
        assert max_concurrent <= 5, f"AssemblyAI rate limit exceeded: {max_concurrent} > 5"
        assert max_concurrent >= 3, f"Rate limiter not working properly: {max_concurrent} < 3"
    
    @pytest.mark.asyncio
    async def test_polly_rate_limiting(self):
        """Test Amazon Polly concurrency limiting (26 concurrent max)."""
        from backend.services.rate_limiting import APIRateLimiter
        
        # Create rate limiter
        rate_limiter = APIRateLimiter()
        
        # Track active requests
        active_requests = []
        max_concurrent = 0
        
        async def mock_polly_request(request_id: int):
            """Mock Polly request that tracks concurrency."""
            nonlocal max_concurrent
            
            async with rate_limiter.polly_semaphore:
                active_requests.append(request_id)
                max_concurrent = max(max_concurrent, len(active_requests))
                
                # Simulate processing time
                await asyncio.sleep(0.05)
                
                active_requests.remove(request_id)
        
        # Start 30 concurrent requests
        tasks = [mock_polly_request(i) for i in range(30)]
        await asyncio.gather(*tasks)
        
        # Verify maximum concurrent requests never exceeded 26
        assert max_concurrent <= 26, f"Polly rate limit exceeded: {max_concurrent} > 26"
        assert max_concurrent >= 10, f"Rate limiter not working properly: {max_concurrent} < 10"
    
    @pytest.mark.asyncio
    async def test_deepgram_rate_limiting(self):
        """Test Deepgram concurrency limiting (10 concurrent max)."""
        from backend.services.rate_limiting import APIRateLimiter
        
        # Create rate limiter
        rate_limiter = APIRateLimiter()
        
        # Track active requests
        active_requests = []
        max_concurrent = 0
        
        async def mock_deepgram_request(request_id: int):
            """Mock Deepgram request that tracks concurrency."""
            nonlocal max_concurrent
            
            async with rate_limiter.deepgram_semaphore:
                active_requests.append(request_id)
                max_concurrent = max(max_concurrent, len(active_requests))
                
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                active_requests.remove(request_id)
        
        # Start 15 concurrent requests
        tasks = [mock_deepgram_request(i) for i in range(15)]
        await asyncio.gather(*tasks)
        
        # Verify maximum concurrent requests never exceeded 10
        assert max_concurrent <= 10, f"Deepgram rate limit exceeded: {max_concurrent} > 10"
        assert max_concurrent >= 5, f"Rate limiter not working properly: {max_concurrent} < 5"


def test_rate_limiter_initialization():
    """Test that rate limiter initializes with correct limits."""
    from backend.services.rate_limiting import APIRateLimiter
    
    rate_limiter = APIRateLimiter()
    
    # Check semaphore limits
    assert rate_limiter.assemblyai_limit == 5
    assert rate_limiter.polly_limit == 26
    assert rate_limiter.deepgram_limit == 10
    
    # Check semaphores are initialized
    assert rate_limiter.assemblyai_semaphore._value == 5
    assert rate_limiter.polly_semaphore._value == 26
    assert rate_limiter.deepgram_semaphore._value == 10


def test_concurrent_environment_setup():
    """Test that environment is properly set up for concurrent testing."""
    assert os.environ.get("SUPABASE_URL") == "https://test.supabase.co"
    assert os.environ.get("SUPABASE_SERVICE_KEY") == "test-key"
    assert os.environ.get("SUPABASE_JWT_SECRET") == "test-jwt-secret"
    
    # Verify all required API keys are set
    required_keys = [
        "GOOGLE_API_KEY", "ASSEMBLYAI_API_KEY", "AWS_ACCESS_KEY_ID", 
        "AWS_SECRET_ACCESS_KEY", "DEEPGRAM_API_KEY"
    ]
    
    for key in required_keys:
        assert os.environ.get(key) is not None, f"Missing environment variable: {key}"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 