"""
System integration tests for the AI interview preparation system.
Tests the integration between components and services.
"""

import os
import pytest
import logging
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models.interview import InterviewStyle
from backend.database.connection import Base
from backend.api import create_app
from backend.services import initialize_services, get_session_manager, get_data_service


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


# Test client fixture
@pytest.fixture
def client():
    """
    Create a test client for the FastAPI application.
    """
    # Create tables in test database
    Base.metadata.create_all(bind=engine)
    
    # Initialize services
    initialize_services({
        "log_level": logging.INFO,
        "test_mode": True
    })
    
    # Create test app
    app = create_app()
    
    # Create test client
    with TestClient(app) as client:
        yield client
    
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)


def test_session_creation(client):
    """Test creating a new interview session."""
    # Create a session
    response = client.post(
        "/api/interview/start",
        json={
            "job_role": "Software Engineer",
            "job_description": "Developing software applications",
            "interview_style": "FORMAL",
            "mode": "interview_with_coaching"
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["job_role"] == "Software Engineer"
    assert data["interview_style"] == "FORMAL"
    assert "welcome_message" in data


def test_message_exchange(client):
    """Test sending messages to an interview session."""
    # Create a session
    create_response = client.post(
        "/api/interview/start",
        json={
            "job_role": "Data Scientist",
            "job_description": "Analyzing data and building models",
            "interview_style": "TECHNICAL",
            "mode": "interview_with_coaching"
        }
    )
    
    # Get session ID
    session_id = create_response.json()["session_id"]
    
    # Send a message
    message_response = client.post(
        "/api/interview/send",
        json={
            "message": "I have experience with Python and machine learning.",
            "session_id": session_id
        }
    )
    
    # Check response
    assert message_response.status_code == 200
    data = message_response.json()
    assert data["session_id"] == session_id
    assert "response" in data
    assert len(data["response"]) > 0


def test_session_management():
    """Test session management service."""
    # Get service instances
    session_manager = get_session_manager()
    
    # Create a session
    session_info = session_manager.create_session(
        mode="interview_only",
        job_role="Product Manager",
        job_description="Managing product development",
        interview_style=InterviewStyle.CASUAL,
        user_id="test-user-123"
    )
    
    # Check session creation
    assert "session_id" in session_info
    session_id = session_info["session_id"]
    
    # Get session
    orchestrator = session_manager.get_session(session_id)
    assert orchestrator is not None
    assert orchestrator.job_role == "Product Manager"
    assert orchestrator.interview_style == InterviewStyle.CASUAL
    
    # List sessions
    sessions = session_manager.list_sessions()
    assert len(sessions) >= 1
    assert any(s["session_id"] == session_id for s in sessions)
    
    # End session
    result = session_manager.end_session(session_id)
    assert result is True
    
    # Check session is not active but still in metadata
    assert session_manager.get_session(session_id) is None
    session_metadata = session_manager.get_session_info(session_id)
    assert session_metadata is not None
    assert session_metadata["active"] is False


def test_data_management():
    """Test data management service."""
    # Get service instances
    data_service = get_data_service()
    
    # Create test conversation history
    conversation_history = [
        {
            "role": "assistant",
            "agent": "interviewer",
            "content": "Tell me about your experience with Python.",
            "timestamp": "2023-09-15T10:00:00"
        },
        {
            "role": "user",
            "content": "I have 5 years of experience with Python.",
            "timestamp": "2023-09-15T10:01:00"
        },
        {
            "role": "assistant",
            "agent": "interviewer",
            "content": "What libraries do you use most frequently?",
            "timestamp": "2023-09-15T10:02:00"
        },
        {
            "role": "user",
            "content": "I use NumPy, Pandas, and TensorFlow.",
            "timestamp": "2023-09-15T10:03:00"
        }
    ]
    
    # Calculate metrics
    metrics = data_service.calculate_session_metrics(conversation_history)
    
    # Check metrics
    assert metrics["total_messages"] == 4
    assert metrics["user_message_count"] == 2
    assert metrics["assistant_message_count"] == 2
    assert metrics["average_user_message_length"] > 0
    assert metrics["average_assistant_message_length"] > 0
    assert metrics["conversation_duration_seconds"] == 180  # 3 minutes


def test_end_to_end_interview(client):
    """Test a complete interview flow."""
    # Create a session
    create_response = client.post(
        "/api/interview/start",
        json={
            "job_role": "Frontend Developer",
            "job_description": "Building user interfaces with React",
            "interview_style": "CASUAL",
            "mode": "interview_only"
        }
    )
    
    # Get session ID
    session_data = create_response.json()
    session_id = session_data["session_id"]
    
    # Send a few messages
    messages = [
        "I have three years of experience with React and JavaScript.",
        "I've built several responsive web applications with modern frameworks.",
        "My most challenging project was a real-time dashboard for data visualization."
    ]
    
    for message in messages:
        response = client.post(
            "/api/interview/send",
            json={
                "message": message,
                "session_id": session_id
            }
        )
        assert response.status_code == 200
    
    # Get conversation history
    history_response = client.get(f"/api/interview/history?session_id={session_id}")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) >= 7  # Welcome + 3 messages + 3 responses
    
    # Get metrics
    metrics_response = client.get(f"/api/interview/metrics?session_id={session_id}")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["total_messages"] >= 7
    
    # End the interview
    end_response = client.post(
        "/api/interview/end",
        json={
            "message": "Thank you for the interview.",
            "session_id": session_id
        }
    )
    
    assert end_response.status_code == 200
    end_data = end_response.json()
    assert "message" in end_data
    assert "metrics" in end_data 