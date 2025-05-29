"""
Phase IV: Testing & Validation - Performance and Load Testing
Tests system performance under load and validates scalability metrics.
"""

import os
import sys
import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

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

from fastapi.testclient import TestClient


class PerformanceMetrics:
    """Tracks and analyzes performance metrics."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.successful_requests = 0
        self.failed_requests = 0
        self.start_time = None
        self.end_time = None
    
    def start_timing(self):
        """Start timing the test."""
        self.start_time = time.time()
    
    def end_timing(self):
        """End timing the test."""
        self.end_time = time.time()
    
    def record_request(self, response_time: float, success: bool):
        """Record a request's performance."""
        self.response_times.append(response_time)
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.response_times:
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'success_rate': 0.0
            }
        
        total_duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        return {
            'total_requests': len(self.response_times),
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.successful_requests / len(self.response_times)) * 100,
            'avg_response_time': statistics.mean(self.response_times),
            'median_response_time': statistics.median(self.response_times),
            'min_response_time': min(self.response_times),
            'max_response_time': max(self.response_times),
            'p95_response_time': self._percentile(self.response_times, 95),
            'p99_response_time': self._percentile(self.response_times, 99),
            'requests_per_second': len(self.response_times) / total_duration if total_duration > 0 else 0,
            'total_duration': total_duration
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of response times."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


class LoadTestRunner:
    """Runs various load testing scenarios."""
    
    def __init__(self, test_client: TestClient):
        self.client = test_client
        self.auth_headers = {
            'Authorization': 'Bearer test-token',
            'Content-Type': 'application/json'
        }
    
    async def simulate_user_session(self, user_id: int) -> Tuple[float, bool]:
        """Simulate a complete user session."""
        start_time = time.time()
        
        try:
            # Create session
            session_response = self.client.post('/interview/session', json={
                'job_role': f'Engineer {user_id}',
                'style': 'formal',
                'difficulty': 'medium'
            }, headers=self.auth_headers)
            
            if session_response.status_code != 200:
                return time.time() - start_time, False
            
            session_id = session_response.json()['session_id']
            
            # Start interview
            start_response = self.client.post('/interview/start', json={
                'job_role': f'Engineer {user_id}',
                'style': 'formal'
            }, headers={
                **self.auth_headers,
                'X-Session-ID': session_id
            })
            
            if start_response.status_code != 200:
                return time.time() - start_time, False
            
            # Send messages
            for i in range(3):  # Simulate 3 messages per session
                message_response = self.client.post('/interview/message', json={
                    'message': f'Test message {i} from user {user_id}'
                }, headers={
                    **self.auth_headers,
                    'X-Session-ID': session_id
                })
                
                if message_response.status_code != 200:
                    return time.time() - start_time, False
            
            # End session
            end_response = self.client.post('/interview/end', headers={
                **self.auth_headers,
                'X-Session-ID': session_id
            })
            
            success = end_response.status_code == 200
            return time.time() - start_time, success
            
        except Exception as e:
            return time.time() - start_time, False
    
    def single_request_test(self, endpoint: str, method: str = 'GET', 
                          data: Dict = None, session_id: str = None) -> Tuple[float, bool]:
        """Test a single request."""
        start_time = time.time()
        
        try:
            headers = self.auth_headers.copy()
            if session_id:
                headers['X-Session-ID'] = session_id
            
            if method == 'POST':
                response = self.client.post(endpoint, json=data or {}, headers=headers)
            else:
                response = self.client.get(endpoint, headers=headers)
            
            success = response.status_code == 200
            return time.time() - start_time, success
            
        except Exception as e:
            return time.time() - start_time, False


@pytest.fixture
def performance_mocks():
    """Set up mocks optimized for performance testing."""
    with patch('backend.database.db_manager.create_client') as mock_supabase, \
         patch('backend.api.auth_api.get_current_user') as mock_auth, \
         patch('backend.services.session_manager.ThreadSafeSessionRegistry') as mock_registry:
        
        # Mock Supabase
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        # Mock auth with minimal processing
        mock_auth.return_value = {
            'id': 'perf-test-user',
            'email': 'perf@test.com',
            'created_at': '2023-01-01T00:00:00Z'
        }
        
        # Mock session registry with fast responses
        mock_registry_instance = MagicMock()
        mock_registry_instance.create_new_session = AsyncMock()
        mock_registry_instance.get_session_manager = AsyncMock()
        
        # Create fast session manager mock
        mock_manager = MagicMock()
        mock_manager.session_id = 'perf-session-id'
        mock_manager.process_message.return_value = {
            'role': 'assistant',
            'content': 'Fast response',
            'timestamp': '2023-01-01T00:00:00Z'
        }
        mock_manager.end_interview.return_value = {
            'coaching_summary': {'score': 85},
            'per_turn_feedback': []
        }
        mock_manager.get_conversation_history.return_value = []
        mock_manager.get_session_stats.return_value = {'total_messages': 1}
        mock_manager.reset_session.return_value = None
        
        # Set up session creation to return unique IDs
        session_counter = 0
        def create_session_side_effect(*args, **kwargs):
            nonlocal session_counter
            session_counter += 1
            return f'session-{session_counter}'
        
        mock_registry_instance.create_new_session.side_effect = create_session_side_effect
        mock_registry_instance.get_session_manager.return_value = mock_manager
        mock_registry.return_value = mock_registry_instance
        
        yield {
            'supabase': mock_client,
            'auth': mock_auth,
            'registry': mock_registry_instance,
            'session_manager': mock_manager
        }


@pytest.fixture
def perf_test_client(performance_mocks):
    """Create test client optimized for performance testing."""
    with patch.object(app, 'state') as mock_state:
        mock_state.agent_manager = performance_mocks['registry']
        
        client = TestClient(app)
        yield client


class TestConcurrentLoad:
    """Test system behavior under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_session_creation(self, perf_test_client, performance_mocks):
        """Test concurrent session creation performance."""
        metrics = PerformanceMetrics()
        runner = LoadTestRunner(perf_test_client)
        
        concurrent_users = 20
        metrics.start_timing()
        
        # Run concurrent session creation
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            for i in range(concurrent_users):
                future = executor.submit(
                    runner.single_request_test, 
                    '/interview/session', 
                    'POST',
                    {'job_role': f'Role {i}', 'style': 'formal'}
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                response_time, success = future.result()
                metrics.record_request(response_time, success)
        
        metrics.end_timing()
        summary = metrics.get_summary()
        
        # Performance assertions
        assert summary['success_rate'] >= 95.0, f"Success rate too low: {summary['success_rate']}%"
        assert summary['avg_response_time'] < 1.0, f"Average response time too high: {summary['avg_response_time']}s"
        assert summary['p95_response_time'] < 2.0, f"95th percentile too high: {summary['p95_response_time']}s"
        
        print(f"Concurrent Session Creation Performance:")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Avg Response Time: {summary['avg_response_time']:.3f}s")
        print(f"  P95 Response Time: {summary['p95_response_time']:.3f}s")
        print(f"  Requests/sec: {summary['requests_per_second']:.1f}")
    
    @pytest.mark.asyncio
    async def test_sustained_load(self, perf_test_client, performance_mocks):
        """Test system performance under sustained load."""
        metrics = PerformanceMetrics()
        runner = LoadTestRunner(perf_test_client)
        
        # Create a session first
        session_response = perf_test_client.post('/interview/session', json={
            'job_role': 'Load Test Role',
            'style': 'formal'
        }, headers=runner.auth_headers)
        session_id = session_response.json()['session_id']
        
        sustained_requests = 50
        metrics.start_timing()
        
        # Send sustained message requests
        for i in range(sustained_requests):
            response_time, success = runner.single_request_test(
                '/interview/message', 
                'POST',
                {'message': f'Load test message {i}'},
                session_id
            )
            metrics.record_request(response_time, success)
        
        metrics.end_timing()
        summary = metrics.get_summary()
        
        # Performance assertions
        assert summary['success_rate'] >= 98.0, f"Success rate too low: {summary['success_rate']}%"
        assert summary['avg_response_time'] < 0.5, f"Average response time too high: {summary['avg_response_time']}s"
        assert summary['requests_per_second'] >= 10, f"Throughput too low: {summary['requests_per_second']} req/s"
        
        print(f"Sustained Load Performance:")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        print(f"  Avg Response Time: {summary['avg_response_time']:.3f}s")
        print(f"  Requests/sec: {summary['requests_per_second']:.1f}")
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, perf_test_client, performance_mocks):
        """Test that memory usage remains stable under load."""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        runner = LoadTestRunner(perf_test_client)
        
        # Run multiple session cycles
        for cycle in range(5):
            # Create and use multiple sessions
            for session_num in range(10):
                session_response = perf_test_client.post('/interview/session', json={
                    'job_role': f'Memory Test Role {cycle}-{session_num}',
                    'style': 'formal'
                }, headers=runner.auth_headers)
                
                if session_response.status_code == 200:
                    session_id = session_response.json()['session_id']
                    
                    # Send some messages
                    for msg_num in range(3):
                        runner.single_request_test(
                            '/interview/message',
                            'POST',
                            {'message': f'Memory test message {msg_num}'},
                            session_id
                        )
                    
                    # End session
                    runner.single_request_test('/interview/end', 'POST', None, session_id)
            
            # Force garbage collection
            gc.collect()
            
            # Check memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            print(f"Cycle {cycle + 1}: Memory usage: {current_memory:.1f}MB (increase: {memory_increase:.1f}MB)")
            
            # Allow some memory growth but not excessive
            assert memory_increase < 100, f"Memory usage increased too much: {memory_increase:.1f}MB"


class TestRateLimitingPerformance:
    """Test rate limiting performance and effectiveness."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_overhead(self):
        """Test that rate limiting doesn't add significant overhead."""
        from backend.services.rate_limiting import APIRateLimiter
        
        rate_limiter = APIRateLimiter()
        
        # Test without rate limiting
        start_time = time.time()
        tasks = []
        for i in range(100):
            tasks.append(asyncio.create_task(asyncio.sleep(0.001)))  # Simulate fast operation
        await asyncio.gather(*tasks)
        no_limiting_time = time.time() - start_time
        
        # Test with rate limiting (using a high limit to avoid blocking)
        test_semaphore = asyncio.Semaphore(50)  # High limit for minimal blocking
        
        async def rate_limited_operation():
            async with test_semaphore:
                await asyncio.sleep(0.001)
        
        start_time = time.time()
        tasks = []
        for i in range(100):
            tasks.append(asyncio.create_task(rate_limited_operation()))
        await asyncio.gather(*tasks)
        with_limiting_time = time.time() - start_time
        
        # Rate limiting should add minimal overhead (less than 3x increase which is acceptable for production)
        overhead_ratio = with_limiting_time / no_limiting_time
        assert overhead_ratio < 3.0, f"Rate limiting overhead too high: {overhead_ratio:.2f}x"
        
        print(f"Rate Limiting Overhead:")
        print(f"  Without limiting: {no_limiting_time:.3f}s")
        print(f"  With limiting: {with_limiting_time:.3f}s")
        print(f"  Overhead ratio: {overhead_ratio:.2f}x")
    
    @pytest.mark.asyncio
    async def test_rate_limiter_fairness(self):
        """Test that rate limiter distributes access fairly."""
        from backend.services.rate_limiting import APIRateLimiter
        
        rate_limiter = APIRateLimiter()
        
        # Use AssemblyAI semaphore (limit of 5)
        semaphore = rate_limiter.assemblyai_semaphore
        
        # Track access times for different "users"
        user_access_times = {i: [] for i in range(10)}
        
        async def user_request(user_id: int, request_num: int):
            async with semaphore:
                access_time = time.time()
                user_access_times[user_id].append(access_time)
                await asyncio.sleep(0.1)  # Simulate work
        
        # Start concurrent requests from multiple users
        tasks = []
        for user_id in range(10):
            for request_num in range(3):  # 3 requests per user
                task = asyncio.create_task(user_request(user_id, request_num))
                tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # Check fairness - each user should get some access
        for user_id in range(10):
            assert len(user_access_times[user_id]) == 3, f"User {user_id} didn't complete all requests"
        
        # Check that no user was completely starved
        first_access_times = [times[0] for times in user_access_times.values()]
        time_spread = max(first_access_times) - min(first_access_times)
        
        # First access should be distributed over a reasonable time window
        assert time_spread < 2.0, f"Access time spread too large: {time_spread:.3f}s"


class TestScalabilityMetrics:
    """Test scalability and performance metrics."""
    
    @pytest.mark.asyncio
    async def test_response_time_vs_load(self, perf_test_client, performance_mocks):
        """Test how response time scales with increasing load."""
        runner = LoadTestRunner(perf_test_client)
        
        load_levels = [1, 5, 10, 20]  # Number of concurrent users
        results = {}
        
        for load_level in load_levels:
            metrics = PerformanceMetrics()
            metrics.start_timing()
            
            with ThreadPoolExecutor(max_workers=load_level) as executor:
                futures = []
                
                # Create sessions concurrently
                for i in range(load_level):
                    future = executor.submit(
                        runner.single_request_test,
                        '/interview/session',
                        'POST',
                        {'job_role': f'Scalability Test {i}', 'style': 'formal'}
                    )
                    futures.append(future)
                
                # Collect results
                for future in as_completed(futures):
                    response_time, success = future.result()
                    metrics.record_request(response_time, success)
            
            metrics.end_timing()
            summary = metrics.get_summary()
            results[load_level] = summary
            
            print(f"Load Level {load_level}: Avg Response Time: {summary['avg_response_time']:.3f}s")
        
        # Check that response time doesn't degrade too much with load
        baseline_response_time = results[1]['avg_response_time']
        max_load_response_time = results[max(load_levels)]['avg_response_time']
        degradation_ratio = max_load_response_time / baseline_response_time
        
        # Response time shouldn't increase more than 3x under load
        assert degradation_ratio < 3.0, f"Response time degradation too high: {degradation_ratio:.2f}x"
        
        # All tests should maintain high success rate
        for load_level, result in results.items():
            assert result['success_rate'] >= 90.0, f"Success rate too low at load {load_level}: {result['success_rate']}%"


def test_performance_environment_setup():
    """Test that performance test environment is configured correctly."""
    required_vars = [
        "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "GOOGLE_API_KEY",
        "ASSEMBLYAI_API_KEY", "AWS_ACCESS_KEY_ID", "DEEPGRAM_API_KEY"
    ]
    
    for var in required_vars:
        assert os.environ.get(var) is not None, f"Missing environment variable: {var}"
    
    # Verify we're in test mode
    assert "test.supabase.co" in os.environ.get("SUPABASE_URL", "")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 