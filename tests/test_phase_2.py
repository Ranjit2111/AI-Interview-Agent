"""
Test suite for Phase II: External API Concurrency Management
Tests rate limiting, database-backed speech tasks, and API concurrency controls.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

# Set test environment variables before imports
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-key"
os.environ["GOOGLE_API_KEY"] = "test-api-key"
os.environ["ASSEMBLYAI_API_KEY"] = "test-assemblyai-key"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "test-aws-key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test-aws-secret"
os.environ["DEEPGRAM_API_KEY"] = "test-deepgram-key"

from backend.services.rate_limiting import APIRateLimiter, get_rate_limiter
from backend.database.db_manager import DatabaseManager
from backend.api.speech.tts_service import TTSService
from backend.api.speech.stt_service import STTService


class TestAPIRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create fresh rate limiter for each test."""
        return APIRateLimiter()
    
    @pytest.mark.asyncio
    async def test_assemblyai_rate_limiting(self, rate_limiter):
        """Test AssemblyAI rate limiting with 5 concurrent slots."""
        # Test acquiring slots
        results = []
        for i in range(7):  # Try to acquire more than the limit
            result = await rate_limiter.acquire_assemblyai()
            results.append(result)
        
        # Should succeed for first 5, fail for remaining 2
        assert sum(results) == 5
        assert results[:5] == [True] * 5
        assert results[5:] == [False] * 2
        
        # Check usage stats
        stats = rate_limiter.get_usage_stats()
        assert stats['assemblyai']['active_connections'] == 5
        assert stats['assemblyai']['available_slots'] == 0
        assert stats['assemblyai']['total_requests'] == 5
        
        # Release some slots and test again
        for _ in range(3):
            rate_limiter.release_assemblyai()
        
        # Should be able to acquire again
        assert await rate_limiter.acquire_assemblyai() == True
        assert await rate_limiter.acquire_assemblyai() == True
        assert await rate_limiter.acquire_assemblyai() == True
        assert await rate_limiter.acquire_assemblyai() == False  # Still at limit
    
    @pytest.mark.asyncio
    async def test_polly_rate_limiting(self, rate_limiter):
        """Test Amazon Polly rate limiting with 26 concurrent slots."""
        # Test acquiring slots up to limit
        acquired_count = 0
        for i in range(30):  # Try to acquire more than the limit
            if await rate_limiter.acquire_polly():
                acquired_count += 1
        
        assert acquired_count == 26
        
        # Check usage stats
        stats = rate_limiter.get_usage_stats()
        assert stats['polly']['active_connections'] == 26
        assert stats['polly']['available_slots'] == 0
    
    @pytest.mark.asyncio
    async def test_deepgram_rate_limiting(self, rate_limiter):
        """Test Deepgram rate limiting with 10 concurrent slots."""
        # Test acquiring slots up to limit
        acquired_count = 0
        for i in range(15):  # Try to acquire more than the limit
            if await rate_limiter.acquire_deepgram():
                acquired_count += 1
        
        assert acquired_count == 10
        
        # Check usage stats
        stats = rate_limiter.get_usage_stats()
        assert stats['deepgram']['active_connections'] == 10
        assert stats['deepgram']['available_slots'] == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_rate_limiting(self, rate_limiter):
        """Test concurrent access to rate limiter."""
        async def acquire_assemblyai():
            return await rate_limiter.acquire_assemblyai()
        
        # Start 10 concurrent tasks
        tasks = [acquire_assemblyai() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Should only allow 5 concurrent connections
        successful_acquisitions = sum(results)
        assert successful_acquisitions == 5
    
    def test_api_availability_check(self, rate_limiter):
        """Test checking API availability."""
        assert rate_limiter.is_api_available('assemblyai') == True
        assert rate_limiter.is_api_available('polly') == True
        assert rate_limiter.is_api_available('deepgram') == True
        assert rate_limiter.is_api_available('unknown') == False


class TestDatabaseBackedSpeechTasks:
    """Test database-backed speech task management."""
    
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
    async def test_create_speech_task(self, db_manager, mock_supabase):
        """Test creating speech processing tasks."""
        # Mock successful response
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"task_id": "test-task-id"}
        ]
        
        task_id = await db_manager.create_speech_task("test-session-id", "stt_batch")
        
        assert task_id == "test-task-id"
        mock_supabase.table.assert_called_with("speech_tasks")
    
    @pytest.mark.asyncio
    async def test_update_speech_task_progress(self, db_manager, mock_supabase):
        """Test updating speech task progress."""
        # Mock successful update
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"updated": True}]
        
        success = await db_manager.update_speech_task(
            "test-task-id",
            "processing",
            progress_data={"step": "uploading", "message": "Uploading audio..."}
        )
        
        assert success is True
        mock_supabase.table.assert_called_with("speech_tasks")
    
    @pytest.mark.asyncio
    async def test_update_speech_task_completion(self, db_manager, mock_supabase):
        """Test updating speech task with final results."""
        # Mock successful update
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"updated": True}]
        
        success = await db_manager.update_speech_task(
            "test-task-id",
            "completed",
            result_data={
                "transcription": "Hello world",
                "confidence": 0.95,
                "language": "en"
            }
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_get_speech_task(self, db_manager, mock_supabase):
        """Test retrieving speech task data."""
        # Mock response data
        mock_data = {
            "task_id": "test-task-id",
            "session_id": "test-session-id",
            "task_type": "stt_batch",
            "status": "completed",
            "result_data": {"transcription": "Hello world"}
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [mock_data]
        
        result = await db_manager.get_speech_task("test-task-id")
        
        assert result is not None
        assert result["task_id"] == "test-task-id"
        assert result["status"] == "completed"
        assert result["result_data"]["transcription"] == "Hello world"
    
    @pytest.mark.asyncio
    async def test_cleanup_completed_tasks(self, db_manager, mock_supabase):
        """Test cleaning up old completed tasks."""
        # Mock successful cleanup
        mock_supabase.table.return_value.delete.return_value.in_.return_value.lt.return_value.execute.return_value.data = [
            {"deleted": "task1"}, {"deleted": "task2"}
        ]
        
        count = await db_manager.cleanup_completed_tasks(24)
        
        assert count == 2


class TestTTSServiceWithRateLimiting:
    """Test TTS service with rate limiting."""
    
    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock rate limiter."""
        mock = AsyncMock()
        mock.acquire_polly.return_value = True
        mock.is_api_available.return_value = True
        return mock
    
    @pytest.fixture
    def mock_polly_client(self):
        """Mock Polly client."""
        mock = Mock()
        mock.synthesize_speech.return_value = {
            "AudioStream": Mock(read=Mock(return_value=b"audio_data"))
        }
        return mock
    
    @pytest.fixture
    def tts_service(self, mock_rate_limiter, mock_polly_client):
        """Create TTS service with mocked dependencies."""
        with patch('backend.services.rate_limiting.get_rate_limiter', return_value=mock_rate_limiter):
            service = TTSService()
            service.polly_client = mock_polly_client
            return service
    
    @pytest.mark.asyncio
    async def test_tts_with_rate_limiting(self, tts_service, mock_rate_limiter, mock_polly_client):
        """Test TTS synthesis with rate limiting."""
        response = await tts_service.synthesize_text("Hello world", "Matthew", 1.0)
        
        # Verify rate limiter was called
        mock_rate_limiter.is_api_available.assert_called_with('polly')
        mock_rate_limiter.acquire_polly.assert_called_once()
        mock_rate_limiter.release_polly.assert_called_once()
        
        # Verify Polly was called
        mock_polly_client.synthesize_speech.assert_called_once()
        
        # Verify response
        assert response.media_type == "audio/mpeg"
    
    @pytest.mark.asyncio
    async def test_tts_rate_limit_unavailable(self, tts_service, mock_rate_limiter):
        """Test TTS when rate limit slots are unavailable."""
        mock_rate_limiter.is_api_available.return_value = False
        
        with pytest.raises(Exception) as exc_info:
            await tts_service.synthesize_text("Hello world", "Matthew", 1.0)
        
        assert "temporarily unavailable due to high demand" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_tts_rate_limit_acquisition_fails(self, tts_service, mock_rate_limiter):
        """Test TTS when rate limit acquisition fails."""
        mock_rate_limiter.acquire_polly.return_value = False
        
        with pytest.raises(Exception) as exc_info:
            await tts_service.synthesize_text("Hello world", "Matthew", 1.0)
        
        assert "rate limiting" in str(exc_info.value)


class TestSTTServiceWithRateLimiting:
    """Test STT service with rate limiting."""
    
    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock rate limiter."""
        mock = AsyncMock()
        mock.acquire_deepgram.return_value = True
        mock.is_api_available.return_value = True
        return mock
    
    @pytest.fixture
    def mock_deepgram_client(self):
        """Mock Deepgram client."""
        return Mock()
    
    @pytest.fixture
    def stt_service(self, mock_rate_limiter, mock_deepgram_client):
        """Create STT service with mocked dependencies."""
        with patch('backend.services.rate_limiting.get_rate_limiter', return_value=mock_rate_limiter):
            service = STTService()
            service.deepgram_client = mock_deepgram_client
            return service
    
    @pytest.mark.asyncio
    async def test_websocket_rate_limiting_unavailable(self, stt_service, mock_rate_limiter):
        """Test WebSocket connection when rate limiting unavailable."""
        mock_rate_limiter.is_api_available.return_value = False
        
        mock_websocket = AsyncMock()
        
        await stt_service.handle_websocket_stream(mock_websocket)
        
        # Should close websocket due to unavailable service
        mock_websocket.close.assert_called_with(code=1008, reason="Service temporarily unavailable due to high demand")
    
    @pytest.mark.asyncio
    async def test_websocket_rate_limit_acquisition_fails(self, stt_service, mock_rate_limiter):
        """Test WebSocket connection when rate limit acquisition fails."""
        mock_rate_limiter.acquire_deepgram.return_value = False
        
        mock_websocket = AsyncMock()
        
        await stt_service.handle_websocket_stream(mock_websocket)
        
        # Should close websocket due to rate limiting
        mock_websocket.close.assert_called_with(code=1008, reason="Service temporarily unavailable due to rate limiting")


class TestConcurrentAPIUsage:
    """Test concurrent API usage scenarios."""
    
    @pytest.mark.asyncio
    async def test_concurrent_assemblyai_requests(self):
        """Test concurrent AssemblyAI requests respect rate limiting."""
        rate_limiter = APIRateLimiter()
        
        async def mock_transcription():
            if await rate_limiter.acquire_assemblyai():
                # Simulate processing time
                await asyncio.sleep(0.1)
                rate_limiter.release_assemblyai()
                return True
            return False
        
        # Start 10 concurrent transcription requests
        tasks = [mock_transcription() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Only 5 should succeed initially due to rate limiting
        successful = sum(results)
        assert successful <= 5
    
    @pytest.mark.asyncio
    async def test_mixed_api_concurrency(self):
        """Test concurrent usage of different APIs."""
        rate_limiter = APIRateLimiter()
        
        # Test that different APIs don't interfere with each other
        assemblyai_acquired = await rate_limiter.acquire_assemblyai()
        polly_acquired = await rate_limiter.acquire_polly()
        deepgram_acquired = await rate_limiter.acquire_deepgram()
        
        assert assemblyai_acquired == True
        assert polly_acquired == True
        assert deepgram_acquired == True
        
        # Check usage stats
        stats = rate_limiter.get_usage_stats()
        assert stats['assemblyai']['active_connections'] == 1
        assert stats['polly']['active_connections'] == 1
        assert stats['deepgram']['active_connections'] == 1


@pytest.mark.asyncio
async def test_speech_api_session_isolation():
    """Test that speech tasks are properly isolated by session."""
    
    # Mock database responses for different sessions
    with patch('backend.database.db_manager.create_client') as mock_create_client:
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock different task IDs for different sessions
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"task_id": "session1-task-id"}
        ]
        
        db_manager = DatabaseManager()
        
        # Create tasks for different sessions
        task1 = await db_manager.create_speech_task("session-1", "stt_batch")
        
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"task_id": "session2-task-id"}
        ]
        
        task2 = await db_manager.create_speech_task("session-2", "stt_batch")
        
        # Tasks should be different
        assert task1 != task2
        assert task1 == "session1-task-id"
        assert task2 == "session2-task-id"


def test_rate_limiter_singleton():
    """Test that get_rate_limiter returns the same instance."""
    limiter1 = get_rate_limiter()
    limiter2 = get_rate_limiter()
    
    assert limiter1 is limiter2


@pytest.mark.asyncio
async def test_error_handling_with_rate_limiting():
    """Test error handling when external APIs fail with rate limiting."""
    rate_limiter = APIRateLimiter()
    
    # Acquire all slots
    for _ in range(5):
        await rate_limiter.acquire_assemblyai()
    
    # Verify no slots available
    assert rate_limiter.is_api_available('assemblyai') == False
    
    # Try to acquire another slot
    result = await rate_limiter.acquire_assemblyai()
    assert result == False
    
    # Check error stats
    stats = rate_limiter.get_usage_stats()
    assert stats['assemblyai']['errors'] == 1


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 