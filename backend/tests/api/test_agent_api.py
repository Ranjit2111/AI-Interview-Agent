"""
Tests for the agent API module.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from backend.api.agent_api import app
from backend.agents.base_agent import BaseAgent
from backend.agents.coach import CoachAgent
from backend.agents.skill_assessor import SkillAssessorAgent


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def mock_coach_agent():
    """Create a mock coach agent."""
    agent = MagicMock(spec=CoachAgent)
    agent.process_input.return_value = {
        "response": "Test coaching response",
        "feedback": "Test feedback"
    }
    return agent


@pytest.fixture
def mock_skill_assessor():
    """Create a mock skill assessor agent."""
    agent = MagicMock(spec=SkillAssessorAgent)
    agent.process_input.return_value = {
        "skills": ["Python", "SQL"],
        "proficiency": {"Python": 0.8, "SQL": 0.7},
        "feedback": "Test assessment feedback"
    }
    return agent


class TestAgentAPI:
    """Tests for the agent API endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    @patch('backend.api.agent_api.CoachAgent')
    def test_coach_endpoint(self, mock_coach_agent_class, client, mock_coach_agent):
        """Test the coach endpoint."""
        # Set up mock
        mock_coach_agent_class.return_value = mock_coach_agent
        
        # Test data
        test_data = {
            "input": "Test coaching input",
            "context": {"session_id": "test_session"}
        }
        
        # Make request
        response = client.post("/coach", json=test_data)
        
        # Verify response
        assert response.status_code == 200
        assert "response" in response.json()
        assert "feedback" in response.json()
        
        # Verify agent was called correctly
        mock_coach_agent.process_input.assert_called_once_with(
            test_data["input"],
            test_data["context"]
        )
    
    @patch('backend.api.agent_api.SkillAssessorAgent')
    def test_skill_assessor_endpoint(self, mock_skill_assessor_class, client, mock_skill_assessor):
        """Test the skill assessor endpoint."""
        # Set up mock
        mock_skill_assessor_class.return_value = mock_skill_assessor
        
        # Test data
        test_data = {
            "input": "Test assessment input",
            "context": {"session_id": "test_session"}
        }
        
        # Make request
        response = client.post("/skill-assessor", json=test_data)
        
        # Verify response
        assert response.status_code == 200
        assert "skills" in response.json()
        assert "proficiency" in response.json()
        assert "feedback" in response.json()
        
        # Verify agent was called correctly
        mock_skill_assessor.process_input.assert_called_once_with(
            test_data["input"],
            test_data["context"]
        )
    
    def test_invalid_input(self, client):
        """Test handling of invalid input."""
        # Test data with missing required fields
        test_data = {
            "input": "Test input"
            # Missing context
        }
        
        # Make request
        response = client.post("/coach", json=test_data)
        
        # Verify error response
        assert response.status_code == 422  # Validation error
    
    def test_agent_error_handling(self, client, mock_coach_agent):
        """Test handling of agent errors."""
        # Set up mock to raise an exception
        mock_coach_agent.process_input.side_effect = Exception("Test error")
        
        # Test data
        test_data = {
            "input": "Test input",
            "context": {"session_id": "test_session"}
        }
        
        # Make request
        response = client.post("/coach", json=test_data)
        
        # Verify error response
        assert response.status_code == 500
        assert "error" in response.json()
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        # Make request
        response = client.options("/coach")
        
        # Verify CORS headers
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make multiple requests quickly
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
        
        # Make one more request that should be rate limited
        response = client.get("/health")
        assert response.status_code == 429  # Too Many Requests
    
    def test_request_validation(self, client):
        """Test request validation."""
        # Test data with invalid types
        test_data = {
            "input": 123,  # Should be string
            "context": "invalid"  # Should be dict
        }
        
        # Make request
        response = client.post("/coach", json=test_data)
        
        # Verify validation error
        assert response.status_code == 422
        assert "error" in response.json()


if __name__ == "__main__":
    pytest.main(["-v"]) 