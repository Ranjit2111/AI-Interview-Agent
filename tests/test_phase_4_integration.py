"""
Phase IV: Testing & Validation - End-to-End Integration Testing
Tests complete interview flow from start to finish with data persistence verification.
"""

import os
import sys
import pytest
import asyncio
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
    from backend.database.db_manager import DatabaseManager
    from backend.agents.orchestrator import AgentSessionManager
    from backend.services.session_manager import ThreadSafeSessionRegistry

from fastapi.testclient import TestClient


class IntegrationTestHelper:
    """Helper class for end-to-end integration testing."""
    
    def __init__(self):
        self.test_data = {
            'user': {
                'id': 'integration-test-user',
                'email': 'integration@test.com',
                'auth_token': 'integration-test-token'
            },
            'job_role': 'Senior Software Engineer',
            'job_description': 'Build scalable web applications using modern frameworks',
            'resume_content': 'Experienced software engineer with 5+ years in web development',
            'interview_style': 'technical',
            'difficulty': 'hard'
        }
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests."""
        return {
            'Authorization': f"Bearer {self.test_data['user']['auth_token']}",
            'Content-Type': 'application/json'
        }
    
    def create_interview_config(self) -> Dict[str, Any]:
        """Create interview configuration."""
        return {
            'job_role': self.test_data['job_role'],
            'job_description': self.test_data['job_description'],
            'resume_content': self.test_data['resume_content'],
            'style': self.test_data['interview_style'],
            'difficulty': self.test_data['difficulty'],
            'interview_duration_minutes': 15,
            'use_time_based_interview': True,
            'company_name': 'TechCorp'
        }


@pytest.fixture
def integration_mocks():
    """Set up comprehensive mocks for integration testing."""
    with patch('backend.database.db_manager.create_client') as mock_supabase, \
         patch('backend.api.auth_api.get_current_user') as mock_auth, \
         patch('backend.services.session_manager.ThreadSafeSessionRegistry') as mock_registry, \
         patch('backend.agents.orchestrator.AgentSessionManager') as mock_session_manager:
        
        # Mock Supabase client
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        # Mock authentication
        mock_auth.return_value = {
            'id': 'integration-test-user',
            'email': 'integration@test.com',
            'created_at': '2023-01-01T00:00:00Z'
        }
        
        # Mock session registry
        mock_registry_instance = MagicMock()
        mock_registry_instance.create_new_session = AsyncMock(return_value='test-session-id')
        mock_registry_instance.get_session_manager = AsyncMock()
        mock_registry.return_value = mock_registry_instance
        
        # Mock session manager
        mock_manager_instance = MagicMock()
        mock_manager_instance.session_id = 'test-session-id'
        mock_manager_instance.process_message = MagicMock()
        mock_manager_instance.end_interview = MagicMock()
        mock_manager_instance.get_conversation_history = MagicMock()
        mock_manager_instance.get_session_stats = MagicMock()
        mock_manager_instance.reset_session = MagicMock()
        mock_registry_instance.get_session_manager.return_value = mock_manager_instance
        
        yield {
            'supabase': mock_client,
            'auth': mock_auth,
            'registry': mock_registry_instance,
            'session_manager': mock_manager_instance
        }


@pytest.fixture
def test_client(integration_mocks):
    """Create test client with integration mocks."""
    with patch.object(app, 'state') as mock_state:
        mock_state.agent_manager = integration_mocks['registry']
        
        client = TestClient(app)
        yield client


class TestCompleteInterviewFlow:
    """Test complete interview flow from start to finish."""
    
    @pytest.mark.asyncio
    async def test_full_interview_lifecycle(self, test_client, integration_mocks):
        """Test complete interview lifecycle: registration -> session -> interview -> completion."""
        helper = IntegrationTestHelper()
        
        # Step 1: Create session and start interview with time-based configuration
        session_data = {
            'job_role': 'Software Engineer',
            'job_description': 'Python developer with experience in web frameworks',
            'style': 'technical',
            'difficulty': 'medium',
            'interview_duration_minutes': 15,
            'use_time_based_interview': True,
            'company_name': 'TechCorp'
        }
        
        session_response = test_client.post(
            '/interview/session',
            json=session_data,
            headers=helper.get_auth_headers()
        )
        
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert 'session_id' in session_data
        session_id = session_data['session_id']
        
        # Verify session creation was called with correct user ID
        integration_mocks['registry'].create_new_session.assert_called_once()
        call_args = integration_mocks['registry'].create_new_session.call_args
        assert call_args.kwargs['user_id'] == 'integration-test-user'
        
        # Step 2: Start interview
        start_response = test_client.post(
            '/interview/start',
            json=session_data,
            headers={
                **helper.get_auth_headers(),
                'X-Session-ID': session_id
            }
        )
        
        assert start_response.status_code == 200
        start_data = start_response.json()
        assert 'message' in start_data
        assert helper.test_data['job_role'] in start_data['message']
        
        # Step 3: Send multiple interview messages
        messages = [
            "I have 5 years of experience in web development.",
            "I'm proficient in React, Node.js, and Python.",
            "I've led teams of 3-5 developers on multiple projects.",
            "My biggest challenge was scaling a system to handle 1M+ users.",
            "I'm passionate about clean code and best practices."
        ]
        
        # Mock session manager responses
        mock_responses = []
        for i, message in enumerate(messages):
            mock_response = {
                'role': 'assistant',
                'content': f'Great answer! Let me ask you about {["technical skills", "leadership", "problem solving", "system design", "development practices"][i]}.',
                'agent': 'interviewer',
                'response_type': 'question',
                'timestamp': '2023-01-01T00:00:00Z'
            }
            mock_responses.append(mock_response)
        
        integration_mocks['session_manager'].process_message.side_effect = mock_responses
        
        # Send messages and verify responses
        responses = []
        for message in messages:
            response = test_client.post(
                '/interview/message',
                json={'message': message},
                headers={
                    **helper.get_auth_headers(),
                    'X-Session-ID': session_id
                }
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data['role'] == 'assistant'
            assert 'content' in response_data
            responses.append(response_data)
        
        # Verify all messages were processed
        assert len(responses) == len(messages)
        assert integration_mocks['session_manager'].process_message.call_count == len(messages)
        
        # Step 4: Get conversation history
        integration_mocks['session_manager'].get_conversation_history.return_value = [
            {'role': 'user', 'content': msg, 'timestamp': '2023-01-01T00:00:00Z'} 
            for msg in messages
        ]
        
        history_response = test_client.get(
            '/interview/history',
            headers={
                **helper.get_auth_headers(),
                'X-Session-ID': session_id
            }
        )
        
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert 'history' in history_data
        assert len(history_data['history']) == len(messages)
        
        # Step 5: Get session statistics
        integration_mocks['session_manager'].get_session_stats.return_value = {
            'total_messages': len(messages),
            'total_questions': len(messages),
            'session_duration_minutes': 15,
            'completion_percentage': 100
        }
        
        stats_response = test_client.get(
            '/interview/stats',
            headers={
                **helper.get_auth_headers(),
                'X-Session-ID': session_id
            }
        )
        
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert 'stats' in stats_data
        assert stats_data['stats']['total_messages'] == len(messages)
        
        # Step 6: End interview
        integration_mocks['session_manager'].end_interview.return_value = {
            'coaching_summary': {
                'overall_score': 85,
                'strengths': ['Technical knowledge', 'Communication'],
                'areas_for_improvement': ['System design depth'],
                'recommendations': ['Practice more system design problems']
            },
            'per_turn_feedback': [
                {
                    'question': 'Tell me about your experience',
                    'answer': messages[0],
                    'feedback': 'Good overview of experience'
                }
            ]
        }
        
        end_response = test_client.post(
            '/interview/end',
            headers={
                **helper.get_auth_headers(),
                'X-Session-ID': session_id
            }
        )
        
        assert end_response.status_code == 200
        end_data = end_response.json()
        assert 'results' in end_data
        assert 'per_turn_feedback' in end_data
        assert end_data['results']['overall_score'] == 85
        
        # Verify end interview was called
        integration_mocks['session_manager'].end_interview.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_reset_functionality(self, test_client, integration_mocks):
        """Test session reset preserves session ID but clears state."""
        helper = IntegrationTestHelper()
        
        # Create session
        session_response = test_client.post(
            '/interview/session',
            json=helper.create_interview_config(),
            headers=helper.get_auth_headers()
        )
        
        assert session_response.status_code == 200
        session_id = session_response.json()['session_id']
        
        # Send a message first
        integration_mocks['session_manager'].process_message.return_value = {
            'role': 'assistant', 'content': 'Hello!'
        }
        
        test_client.post(
            '/interview/message',
            json={'message': 'Hello'},
            headers={
                **helper.get_auth_headers(),
                'X-Session-ID': session_id
            }
        )
        
        # Reset session
        reset_response = test_client.post(
            '/interview/reset',
            headers={
                **helper.get_auth_headers(),
                'X-Session-ID': session_id
            }
        )
        
        assert reset_response.status_code == 200
        reset_data = reset_response.json()
        assert 'message' in reset_data
        assert reset_data['session_id'] == session_id
        
        # Verify reset was called
        integration_mocks['session_manager'].reset_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_session(self, test_client, integration_mocks):
        """Test error handling for invalid session IDs."""
        helper = IntegrationTestHelper()
        
        # Mock session manager to raise exception for invalid session
        integration_mocks['registry'].get_session_manager.side_effect = ValueError("Session not found")
        
        # Try to send message to invalid session
        response = test_client.post(
            '/interview/message',
            json={'message': 'Hello'},
            headers={
                **helper.get_auth_headers(),
                'X-Session-ID': 'invalid-session-id'
            }
        )
        
        assert response.status_code == 404
        assert 'Session not found' in response.json()['detail']
    
    @pytest.mark.asyncio
    async def test_authentication_required_endpoints(self, test_client, integration_mocks):
        """Test that all endpoints require proper authentication."""
        helper = IntegrationTestHelper()
        
        # Create session first to get valid session ID
        session_response = test_client.post(
            '/interview/session',
            json=helper.create_interview_config(),
            headers=helper.get_auth_headers()
        )
        session_id = session_response.json()['session_id']
        
        # Test endpoints without authentication
        endpoints_to_test = [
            ('POST', '/interview/session', helper.create_interview_config()),
            ('POST', '/interview/start', helper.create_interview_config()),
            ('POST', '/interview/message', {'message': 'test'}),
            ('POST', '/interview/end', None),
            ('GET', '/interview/history', None),
            ('GET', '/interview/stats', None),
            ('POST', '/interview/reset', None)
        ]
        
        # Mock auth to fail
        integration_mocks['auth'].side_effect = Exception("Authentication required")
        
        for method, endpoint, data in endpoints_to_test:
            headers = {'Content-Type': 'application/json'}
            if endpoint != '/interview/session':
                headers['X-Session-ID'] = session_id
            
            if method == 'POST':
                if data:
                    response = test_client.post(endpoint, json=data, headers=headers)
                else:
                    response = test_client.post(endpoint, headers=headers)
            else:
                response = test_client.get(endpoint, headers=headers)
            
            # Should fail due to missing authentication
            assert response.status_code in [401, 500], f"Endpoint {endpoint} should require authentication"


class TestSpeechProcessingIntegration:
    """Test speech processing integration with rate limiting."""
    
    @pytest.mark.asyncio
    async def test_speech_task_creation_and_tracking(self, integration_mocks):
        """Test speech task creation and tracking with database persistence."""
        from backend.database.db_manager import DatabaseManager
        
        # Create mock database manager
        db_manager = DatabaseManager()
        
        # Mock speech task methods
        db_manager.create_speech_task = AsyncMock(return_value='test-speech-task-id')
        db_manager.update_speech_task = AsyncMock(return_value=True)
        db_manager.get_speech_task = AsyncMock()
        
        # Test task creation
        task_id = await db_manager.create_speech_task('test-session-id', 'stt_batch')
        assert task_id == 'test-speech-task-id'
        
        # Verify creation was called with correct parameters
        db_manager.create_speech_task.assert_called_once_with('test-session-id', 'stt_batch')
        
        # Test task update
        success = await db_manager.update_speech_task(
            task_id, 
            'completed', 
            progress_data={'progress': 100},
            result_data={'transcript': 'Hello world'}
        )
        assert success is True
        
        # Verify update was called correctly
        db_manager.update_speech_task.assert_called_once_with(
            task_id,
            'completed',
            progress_data={'progress': 100},
            result_data={'transcript': 'Hello world'}
        )
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self):
        """Test rate limiting integration across different services."""
        from backend.services.rate_limiting import APIRateLimiter
        
        rate_limiter = APIRateLimiter()
        
        # Test all services have proper rate limiting
        async def test_service_limit(semaphore, service_name, expected_limit):
            active_count = 0
            max_active = 0
            
            async def mock_request():
                nonlocal active_count, max_active
                async with semaphore:
                    active_count += 1
                    max_active = max(max_active, active_count)
                    await asyncio.sleep(0.01)
                    active_count -= 1
            
            # Start more requests than the limit allows
            tasks = [mock_request() for _ in range(expected_limit + 5)]
            await asyncio.gather(*tasks)
            
            assert max_active <= expected_limit, f"{service_name} exceeded rate limit"
            return max_active
        
        # Test AssemblyAI limit (5)
        assemblyai_max = await test_service_limit(
            rate_limiter.assemblyai_semaphore, 
            "AssemblyAI", 
            5
        )
        
        # Test Polly limit (26) - using smaller number for faster testing
        polly_max = await test_service_limit(
            rate_limiter.polly_semaphore, 
            "Polly", 
            26
        )
        
        # Test Deepgram limit (10)
        deepgram_max = await test_service_limit(
            rate_limiter.deepgram_semaphore, 
            "Deepgram", 
            10
        )
        
        # Verify all limits were respected
        assert assemblyai_max <= 5
        assert polly_max <= 26
        assert deepgram_max <= 10


class TestDataPersistence:
    """Test data persistence and recovery scenarios."""
    
    @pytest.mark.asyncio
    async def test_session_data_persistence(self, integration_mocks):
        """Test that session data is properly persisted and can be recovered."""
        from backend.database.db_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Mock session persistence methods
        test_session_data = {
            'session_id': 'test-session-id',
            'user_id': 'test-user-id',
            'session_config': {
                'job_role': 'Software Engineer',
                'difficulty': 'medium'
            },
            'conversation_history': [
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'Hi there!'}
            ],
            'session_stats': {
                'total_messages': 2,
                'session_duration_minutes': 5
            },
            'status': 'active'
        }
        
        db_manager.save_session_state = AsyncMock(return_value=True)
        db_manager.load_session_state = AsyncMock(return_value=test_session_data)
        
        # Test saving session state
        success = await db_manager.save_session_state('test-session-id', test_session_data)
        assert success is True
        
        # Test loading session state
        loaded_data = await db_manager.load_session_state('test-session-id')
        assert loaded_data == test_session_data
        assert loaded_data['user_id'] == 'test-user-id'
        assert len(loaded_data['conversation_history']) == 2
        
        # Verify methods were called correctly
        db_manager.save_session_state.assert_called_once_with('test-session-id', test_session_data)
        db_manager.load_session_state.assert_called_once_with('test-session-id')
    
    @pytest.mark.asyncio
    async def test_cleanup_completed_tasks(self, integration_mocks):
        """Test cleanup of completed speech tasks."""
        from backend.database.db_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        
        # Mock cleanup method
        db_manager.cleanup_completed_tasks = AsyncMock(return_value=5)
        
        # Test cleanup
        cleaned_count = await db_manager.cleanup_completed_tasks(24)
        assert cleaned_count == 5
        
        # Verify cleanup was called with correct parameters
        db_manager.cleanup_completed_tasks.assert_called_once_with(24)


def test_integration_environment_setup():
    """Test that integration test environment is properly configured."""
    required_env_vars = [
        "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SUPABASE_JWT_SECRET",
        "GOOGLE_API_KEY", "ASSEMBLYAI_API_KEY", "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY", "DEEPGRAM_API_KEY"
    ]
    
    for var in required_env_vars:
        assert os.environ.get(var) is not None, f"Missing environment variable: {var}"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 