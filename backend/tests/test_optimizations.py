"""
Test suite for verifying performance optimizations in the AI Interviewer system.
These tests focus on measuring the performance improvements from caching and optimizations.
"""

import pytest
import time
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

from backend.agents.orchestrator import Orchestrator, OrchestratorMode
from backend.services.session_manager import SessionManager
from backend.services.data_management import DataManagementService
from backend.utils.event_bus import EventBus
from backend.models.interview import InterviewSession, Question, Answer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def event_bus():
    """Create an event bus for testing."""
    return EventBus()

@pytest.fixture
def orchestrator():
    """Create an orchestrator instance for testing."""
    session_id = str(uuid.uuid4())
    job_role = "Software Engineer"
    return Orchestrator(
        session_id=session_id,
        job_role=job_role,
        interview_style="technical",
        mode=OrchestratorMode.INTERVIEW,
        event_bus=EventBus(),
        logger=logger
    )

@pytest.fixture
def session_manager():
    """Create a session manager instance for testing."""
    return SessionManager(
        event_bus=EventBus(),
        logger=logger
    )

@pytest.fixture
def data_service():
    """Create a data management service instance for testing."""
    return DataManagementService(
        event_bus=EventBus(),
        logger=logger
    )

def test_orchestrator_caching(orchestrator):
    """Test response caching in the orchestrator."""
    # First message - should be processed normally
    start_time = time.time()
    response1 = orchestrator.process_message("Tell me about your experience with Python.")
    first_time = time.time() - start_time
    
    # Same message again - should use cache
    start_time = time.time()
    response2 = orchestrator.process_message("Tell me about your experience with Python.")
    cached_time = time.time() - start_time
    
    # Assert that cached response is much faster
    assert cached_time < first_time, "Cached response should be faster than original"
    logging.info(f"Original response time: {first_time:.4f}s, Cached response time: {cached_time:.4f}s")
    
    # The content should be the same between responses
    assert response1["content"] == response2["content"], "Cached response content should match original"
    
    # But timestamps should be different
    assert response1["timestamp"] != response2["timestamp"], "Timestamps should be different"

def test_conversation_history_optimization(orchestrator):
    """Test conversation history optimization with long conversations."""
    # Add enough messages to trigger summarization
    for i in range(25):  # More than window size
        if i % 2 == 0:
            orchestrator.conversation_history.append({
                "role": "user",
                "content": f"User message {i}",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            orchestrator.conversation_history.append({
                "role": "assistant",
                "content": f"Assistant response {i}",
                "agent": "interviewer",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    # Get optimized history
    relevant_history = orchestrator._get_relevant_history()
    
    # Assert summary was created and history was optimized
    assert len(relevant_history) < len(orchestrator.conversation_history), "Relevant history should be shorter than full history"
    assert any(msg.get("is_summary") for msg in relevant_history), "Summary should be included in relevant history"
    
    # First message should be the summary
    assert relevant_history[0].get("role") == "system", "First message should be system summary"
    assert "History summary" in relevant_history[0].get("content", ""), "Summary should contain history summary text"

def test_data_management_caching(data_service):
    """Test caching in the data management service."""
    # Create test conversation history
    conversation_history = []
    for i in range(10):
        if i % 2 == 0:
            conversation_history.append({
                "role": "user",
                "content": f"This is test message {i}",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            conversation_history.append({
                "role": "assistant",
                "content": f"This is response {i}",
                "agent": "interviewer" if i < 5 else "skill_assessor",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    # First call to calculate metrics
    start_time = time.time()
    metrics1 = data_service.calculate_session_metrics(conversation_history)
    first_time = time.time() - start_time
    
    # Second call - should use cache
    start_time = time.time()
    metrics2 = data_service.calculate_session_metrics(conversation_history)
    cached_time = time.time() - start_time
    
    # Assert that cached calculation is faster
    assert cached_time < first_time, "Cached metrics calculation should be faster"
    logging.info(f"Original metrics time: {first_time:.4f}s, Cached metrics time: {cached_time:.4f}s")
    
    # Metrics should be identical
    assert metrics1 == metrics2, "Cached metrics should match original metrics"
    
    # Test QA pair extraction caching
    start_time = time.time()
    qa_pairs1 = data_service._extract_qa_pairs_cached(conversation_history)
    first_qa_time = time.time() - start_time
    
    start_time = time.time()
    qa_pairs2 = data_service._extract_qa_pairs_cached(conversation_history)
    cached_qa_time = time.time() - start_time
    
    # Assert that cached QA extraction is faster
    assert cached_qa_time < first_qa_time, "Cached QA extraction should be faster"
    logging.info(f"Original QA extraction time: {first_qa_time:.4f}s, Cached extraction time: {cached_qa_time:.4f}s")

def test_session_manager_caching(session_manager, monkeypatch):
    """Test session list caching in session manager."""
    # Mock the database lookup to make it measurable
    def mock_query_all(self):
        time.sleep(0.1)  # Simulate database query time
        return []
    
    # Apply the mock
    monkeypatch.setattr("sqlalchemy.orm.Query.all", mock_query_all)
    
    # First call to list sessions - should query "database"
    start_time = time.time()
    sessions1 = session_manager.list_sessions(None)
    first_time = time.time() - start_time
    
    # Second call - should use cache
    start_time = time.time()
    sessions2 = session_manager.list_sessions(None)
    cached_time = time.time() - start_time
    
    # Assert that cached call is faster
    assert cached_time < first_time, "Cached session listing should be faster"
    assert cached_time < 0.05, "Cached call should be near-instant"
    logging.info(f"Original session list time: {first_time:.4f}s, Cached time: {cached_time:.4f}s")

def test_orchestrator_message_hashing(orchestrator):
    """Test message hashing optimization."""
    # Generate a hash for a message
    message = "This is a test message that should be hashed efficiently"
    
    # First hash calculation
    start_time = time.time()
    hash1 = orchestrator._get_message_hash(message)
    first_time = time.time() - start_time
    
    # Second hash calculation - should use cache
    start_time = time.time()
    hash2 = orchestrator._get_message_hash(message)
    cached_time = time.time() - start_time
    
    # Assert that cached hash calculation is faster
    assert cached_time < first_time, "Cached hash calculation should be faster"
    assert hash1 == hash2, "Hash values should be identical"
    logging.info(f"Original hash time: {first_time:.4f}s, Cached hash time: {cached_time:.4f}s")

def test_conversation_hash_performance(orchestrator):
    """Test conversation hash performance."""
    # Add messages to conversation history
    for i in range(10):
        orchestrator.conversation_history.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message content {i}" * 10,  # Make content longer
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Measure hash calculation time
    start_time = time.time()
    hash_value = orchestrator._get_conversation_hash()
    hash_time = time.time() - start_time
    
    # Assert hash calculation is fast
    assert hash_time < 0.01, "Conversation hash calculation should be fast"
    assert isinstance(hash_value, str), "Hash should be a string"
    assert len(hash_value) > 0, "Hash should not be empty"
    logging.info(f"Conversation hash calculation time: {hash_time:.6f}s")

def test_orchestrator_reset(orchestrator):
    """Test that orchestrator reset properly clears caches."""
    # Add some test data
    orchestrator.conversation_history.append({
        "role": "user",
        "content": "Test message",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Cache a test message hash
    test_message = "Message to cache"
    orchestrator._get_message_hash(test_message)
    
    # Reset the orchestrator
    orchestrator.reset()
    
    # Verify caches are cleared
    assert len(orchestrator.conversation_history) == 0, "Conversation history should be empty after reset"
    assert len(orchestrator._message_hash_cache) == 0, "Message hash cache should be empty after reset"
    assert orchestrator._response_cache == {}, "Response cache should be empty after reset"
    assert orchestrator._summarized_history is None, "Summarized history should be None after reset" 