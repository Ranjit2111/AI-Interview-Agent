"""
Tests for the resource recommender agent module.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from backend.agents.resource_recommender import ResourceRecommenderAgent


@pytest.fixture
def resource_recommender():
    """Create a resource recommender agent instance for testing."""
    return ResourceRecommenderAgent()


@pytest.fixture
def mock_gemini():
    """Create a mock Gemini model."""
    with patch('backend.agents.resource_recommender.GoogleGenerativeAI') as mock:
        model = MagicMock()
        model.generate_content.return_value = MagicMock(
            text="Test resource recommendations"
        )
        mock.return_value = model
        yield mock


class TestResourceRecommenderAgent:
    """Tests for the ResourceRecommenderAgent class."""
    
    def test_initialization(self, resource_recommender, mock_gemini):
        """Test that resource recommender agent initializes properly."""
        assert resource_recommender.model is not None
        assert resource_recommender.context is not None
        assert resource_recommender.resource_database is not None
        assert isinstance(resource_recommender.resource_database, dict)
    
    def test_process_input(self, resource_recommender, mock_gemini):
        """Test processing resource recommendation input."""
        # Test input
        test_input = "I need resources to learn Python"
        test_context = {
            "session_id": "test_session",
            "skills": ["Python"],
            "proficiency": {"Python": 0.3}
        }
        
        # Process input
        result = resource_recommender.process_input(test_input, test_context)
        
        # Verify result
        assert result is not None
        assert "recommendations" in result
        assert "learning_path" in result
        assert "resources" in result
        assert isinstance(result["recommendations"], list)
        assert isinstance(result["learning_path"], list)
        assert isinstance(result["resources"], list)
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_recommendations(self, resource_recommender, mock_gemini):
        """Test recommendation generation."""
        # Test data
        test_data = {
            "skills": ["Python", "SQL"],
            "proficiency": {"Python": 0.3, "SQL": 0.5}
        }
        
        # Generate recommendations
        recommendations = resource_recommender._generate_recommendations(test_data)
        
        # Verify recommendations
        assert recommendations is not None
        assert isinstance(recommendations, dict)
        assert "recommendations" in recommendations
        assert "learning_path" in recommendations
        assert "resources" in recommendations
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_generate_learning_path(self, resource_recommender, mock_gemini):
        """Test learning path generation."""
        # Test data
        test_data = {
            "skill": "Python",
            "proficiency": 0.3,
            "goals": ["web development", "data analysis"]
        }
        
        # Generate learning path
        learning_path = resource_recommender._generate_learning_path(test_data)
        
        # Verify learning path
        assert learning_path is not None
        assert isinstance(learning_path, list)
        assert len(learning_path) > 0
        assert all(isinstance(step, dict) for step in learning_path)
        assert all("title" in step for step in learning_path)
        assert all("description" in step for step in learning_path)
        
        # Verify model was called
        mock_gemini.return_value.generate_content.assert_called_once()
    
    def test_find_resources(self, resource_recommender):
        """Test resource finding."""
        # Test data
        test_data = {
            "skill": "Python",
            "level": "beginner",
            "type": "tutorial"
        }
        
        # Find resources
        resources = resource_recommender._find_resources(test_data)
        
        # Verify resources
        assert resources is not None
        assert isinstance(resources, list)
        assert len(resources) > 0
        assert all(isinstance(r, dict) for r in resources)
        assert all("title" in r for r in resources)
        assert all("url" in r for r in resources)
    
    def test_context_management(self, resource_recommender):
        """Test context management in resource recommender."""
        # Add some messages
        resource_recommender.context.add_message("user", "Hello")
        resource_recommender.context.add_message("assistant", "Hi there!")
        
        # Verify context state
        assert len(resource_recommender.context.messages) == 2
        assert resource_recommender.context.messages[0]["content"] == "Hello"
        assert resource_recommender.context.messages[1]["content"] == "Hi there!"
    
    def test_error_handling(self, resource_recommender, mock_gemini):
        """Test error handling in resource recommender."""
        # Set up mock to raise an exception
        mock_gemini.return_value.generate_content.side_effect = Exception("Test error")
        
        # Test input
        test_input = "Recommend resources"
        test_context = {"session_id": "test_session"}
        
        # Process input (should handle error gracefully)
        result = resource_recommender.process_input(test_input, test_context)
        
        # Verify error handling
        assert result is not None
        assert "error" in result
        assert isinstance(result["error"], str)
    
    def test_resource_database(self, resource_recommender):
        """Test resource database structure."""
        # Verify database structure
        assert "tutorials" in resource_recommender.resource_database
        assert "courses" in resource_recommender.resource_database
        assert "books" in resource_recommender.resource_database
        
        # Verify resource types
        for resource_type in resource_recommender.resource_database.values():
            assert isinstance(resource_type, dict)
            assert "beginner" in resource_type
            assert "intermediate" in resource_type
            assert "advanced" in resource_type
    
    def test_resource_filtering(self, resource_recommender):
        """Test resource filtering."""
        # Test cases
        test_cases = [
            ({"level": "beginner", "type": "tutorial"}, "tutorials"),
            ({"level": "intermediate", "type": "course"}, "courses"),
            ({"level": "advanced", "type": "book"}, "books")
        ]
        
        for criteria, expected_type in test_cases:
            resources = resource_recommender._filter_resources(criteria)
            assert all(r["type"] == expected_type for r in resources)
    
    def test_learning_path_validation(self, resource_recommender):
        """Test learning path validation."""
        # Test data
        test_path = [
            {"title": "Step 1", "description": "Description 1"},
            {"title": "Step 2", "description": "Description 2"}
        ]
        
        # Validate path
        is_valid = resource_recommender._validate_learning_path(test_path)
        
        # Verify validation
        assert is_valid is True
        assert all("title" in step for step in test_path)
        assert all("description" in step for step in test_path)
    
    def test_resource_ranking(self, resource_recommender):
        """Test resource ranking."""
        # Test data
        test_resources = [
            {"title": "Resource 1", "rating": 4.5},
            {"title": "Resource 2", "rating": 4.0},
            {"title": "Resource 3", "rating": 3.5}
        ]
        
        # Rank resources
        ranked = resource_recommender._rank_resources(test_resources)
        
        # Verify ranking
        assert len(ranked) == len(test_resources)
        assert ranked[0]["rating"] >= ranked[1]["rating"]
        assert ranked[1]["rating"] >= ranked[2]["rating"]


if __name__ == "__main__":
    pytest.main(["-v"]) 