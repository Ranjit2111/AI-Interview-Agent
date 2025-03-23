"""
Performance tests for the AI interview preparation system.
Tests system performance and identifies bottlenecks.
"""

import os
import pytest
import logging
import time
import random
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

from backend.database.connection import Base, get_db
from backend.services import initialize_services, get_session_manager, get_data_service
from backend.models.interview import InterviewStyle
from backend.agents import OrchestratorMode
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create in-memory test database
TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db_session():
    """Create database tables and yield a test database session."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = TestSessionLocal()
    
    # Initialize services
    initialize_services({
        "log_level": logging.INFO,
        "test_mode": True
    })
    
    yield db
    
    # Clean up
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session_manager():
    """Get the session manager service."""
    return get_session_manager()


@pytest.fixture
def data_service():
    """Get the data management service."""
    return get_data_service()


def test_session_creation_performance(session_manager, db_session):
    """Test the performance of creating interview sessions."""
    # Test parameters
    num_sessions = 10
    creation_times = []
    
    # Create sessions and measure time
    for i in range(num_sessions):
        job_role = f"Software Engineer {i}"
        start_time = time.time()
        
        session_info = session_manager.create_session(
            mode=OrchestratorMode.INTERVIEW_WITH_COACHING,
            job_role=job_role,
            job_description="Developing software applications",
            interview_style=InterviewStyle.FORMAL,
            user_id=f"user-{i}"
        )
        
        end_time = time.time()
        creation_times.append(end_time - start_time)
    
    # Calculate statistics
    avg_time = sum(creation_times) / len(creation_times)
    max_time = max(creation_times)
    min_time = min(creation_times)
    
    # Log performance metrics
    logger.info(f"Session creation performance:")
    logger.info(f"Average time: {avg_time:.4f} seconds")
    logger.info(f"Maximum time: {max_time:.4f} seconds")
    logger.info(f"Minimum time: {min_time:.4f} seconds")
    
    # Assert that session creation is reasonably fast
    assert avg_time < 0.5, f"Average session creation time ({avg_time:.4f}s) exceeds threshold (0.5s)"
    

def test_session_retrieval_performance(session_manager, db_session):
    """Test the performance of retrieving session information."""
    # Create test sessions
    num_sessions = 10
    session_ids = []
    
    for i in range(num_sessions):
        session_info = session_manager.create_session(
            mode=OrchestratorMode.INTERVIEW_WITH_COACHING,
            job_role=f"Software Engineer {i}",
            job_description="Developing software applications",
            interview_style=InterviewStyle.FORMAL,
            user_id=f"user-{i}"
        )
        session_ids.append(session_info["session_id"])
    
    # Test session retrieval performance
    retrieval_times = []
    for session_id in session_ids:
        start_time = time.time()
        
        session_info = session_manager.get_session_info(session_id)
        
        end_time = time.time()
        retrieval_times.append(end_time - start_time)
    
    # Calculate statistics
    avg_time = sum(retrieval_times) / len(retrieval_times)
    max_time = max(retrieval_times)
    min_time = min(retrieval_times)
    
    # Log performance metrics
    logger.info(f"Session retrieval performance:")
    logger.info(f"Average time: {avg_time:.4f} seconds")
    logger.info(f"Maximum time: {max_time:.4f} seconds")
    logger.info(f"Minimum time: {min_time:.4f} seconds")
    
    # Assert that session retrieval is fast
    assert avg_time < 0.1, f"Average session retrieval time ({avg_time:.4f}s) exceeds threshold (0.1s)"


def test_data_management_performance(data_service, db_session):
    """Test the performance of calculating metrics and archiving sessions."""
    # Create sample conversation history
    conversation_history = []
    num_messages = 20
    
    for i in range(num_messages):
        if i % 2 == 0:
            # Interviewer message
            conversation_history.append({
                "role": "assistant",
                "content": f"Interview question {i//2}",
                "agent": "interviewer",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime(time.time() - (num_messages - i) * 60))
            })
        else:
            # User message
            conversation_history.append({
                "role": "user",
                "content": f"Answer to question {i//2}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime(time.time() - (num_messages - i) * 60))
            })
    
    # Test metrics calculation performance
    metrics_times = []
    for _ in range(5):  # Run 5 times to get average
        start_time = time.time()
        
        metrics = data_service.calculate_session_metrics(conversation_history)
        
        end_time = time.time()
        metrics_times.append(end_time - start_time)
    
    # Calculate statistics for metrics calculation
    avg_metrics_time = sum(metrics_times) / len(metrics_times)
    
    # Log performance metrics
    logger.info(f"Metrics calculation performance:")
    logger.info(f"Average time: {avg_metrics_time:.4f} seconds")
    
    # Assert that metrics calculation is reasonably fast
    assert avg_metrics_time < 0.1, f"Average metrics calculation time ({avg_metrics_time:.4f}s) exceeds threshold (0.1s)"


def test_list_sessions_performance(session_manager, db_session):
    """Test the performance of listing sessions."""
    # Create test sessions
    num_sessions = 20
    user_id = "performance-test-user"
    
    for i in range(num_sessions):
        session_manager.create_session(
            mode=OrchestratorMode.INTERVIEW_WITH_COACHING,
            job_role=f"Software Engineer {i}",
            job_description="Developing software applications",
            interview_style=InterviewStyle.FORMAL,
            user_id=user_id
        )
    
    # Test session listing performance
    list_times = []
    for _ in range(5):  # Run 5 times to get average
        start_time = time.time()
        
        sessions = session_manager.list_sessions(user_id=user_id)
        
        end_time = time.time()
        list_times.append(end_time - start_time)
    
    # Calculate statistics
    avg_time = sum(list_times) / len(list_times)
    
    # Log performance metrics
    logger.info(f"Session listing performance:")
    logger.info(f"Average time: {avg_time:.4f} seconds")
    logger.info(f"Number of sessions: {len(sessions)}")
    
    # Assert that session listing is reasonably fast
    assert avg_time < 0.2, f"Average session listing time ({avg_time:.4f}s) exceeds threshold (0.2s)"


def test_session_cleanup_performance(session_manager, db_session):
    """Test the performance of cleaning up inactive sessions."""
    # Create test sessions with varying creation times
    num_sessions = 20
    
    # Mock datetime.utcnow to control session creation times
    with patch('backend.models.interview.datetime') as mock_datetime:
        for i in range(num_sessions):
            # Set creation time progressively older
            # Half of the sessions will be older than 24 hours
            hours_ago = i * 2  # 0, 2, 4, ..., 38 hours ago
            mock_datetime.utcnow.return_value = time.gmtime(time.time() - hours_ago * 3600)
            
            session_manager.create_session(
                mode=OrchestratorMode.INTERVIEW_WITH_COACHING,
                job_role=f"Software Engineer {i}",
                job_description="Developing software applications",
                interview_style=InterviewStyle.FORMAL,
                user_id=f"user-{i}"
            )
    
    # Test cleanup performance
    start_time = time.time()
    
    removed_count = session_manager.cleanup_inactive_sessions(max_age_hours=24)
    
    end_time = time.time()
    cleanup_time = end_time - start_time
    
    # Log performance metrics
    logger.info(f"Session cleanup performance:")
    logger.info(f"Time taken: {cleanup_time:.4f} seconds")
    logger.info(f"Sessions cleaned up: {removed_count}")
    
    # Assert that cleanup is reasonably fast
    assert cleanup_time < 0.5, f"Session cleanup time ({cleanup_time:.4f}s) exceeds threshold (0.5s)"


def test_conversation_history_performance(session_manager, db_session):
    """Test the performance of accessing and updating conversation history."""
    # Create a test session
    session_info = session_manager.create_session(
        mode=OrchestratorMode.INTERVIEW_WITH_COACHING,
        job_role="Software Engineer",
        job_description="Developing software applications",
        interview_style=InterviewStyle.FORMAL,
        user_id="user-test"
    )
    
    session_id = session_info["session_id"]
    orchestrator = session_manager.get_session(session_id)
    
    # Add messages to conversation history
    num_messages = 50
    update_times = []
    
    for i in range(num_messages):
        message = f"Test message {i}"
        
        start_time = time.time()
        
        if i % 2 == 0:
            # Add as user message
            orchestrator.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
            })
        else:
            # Add as assistant message
            orchestrator.conversation_history.append({
                "role": "assistant",
                "content": message,
                "agent": "interviewer",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
            })
        
        end_time = time.time()
        update_times.append(end_time - start_time)
    
    # Test accessing conversation history
    start_time = time.time()
    
    history = orchestrator.conversation_history
    
    end_time = time.time()
    access_time = end_time - start_time
    
    # Calculate statistics
    avg_update_time = sum(update_times) / len(update_times)
    
    # Log performance metrics
    logger.info(f"Conversation history performance:")
    logger.info(f"Average update time: {avg_update_time:.4f} seconds")
    logger.info(f"Access time: {access_time:.4f} seconds")
    logger.info(f"History length: {len(history)}")
    
    # Assert that history operations are fast
    assert avg_update_time < 0.01, f"Average history update time ({avg_update_time:.4f}s) exceeds threshold (0.01s)"
    assert access_time < 0.01, f"History access time ({access_time:.4f}s) exceeds threshold (0.01s)" 