"""
Unit tests for the search service.
Tests the functionality of the search service for finding learning resources.
"""

import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from backend.services.search_service import (
    SearchService, 
    SerpApiProvider, 
    SerperProvider,
    Resource,
    ResourceType
)


# Sample search response data
SERPAPI_SAMPLE_RESPONSE = {
    "organic_results": [
        {
            "position": 1,
            "title": "Learn Python Programming - Beginner's Guide",
            "link": "https://www.example.com/python-tutorial",
            "snippet": "A comprehensive guide to learning Python programming from scratch. Perfect for beginners.",
            "displayed_link": "www.example.com › python-tutorial"
        },
        {
            "position": 2,
            "title": "Python Beginner Course - Coursera",
            "link": "https://www.coursera.org/learn/python",
            "snippet": "Start learning Python with this beginner-friendly course. No prior experience required.",
            "displayed_link": "www.coursera.org › learn › python"
        }
    ]
}

SERPER_SAMPLE_RESPONSE = {
    "organic": [
        {
            "position": 1,
            "title": "Learn Python Programming - Beginner's Guide",
            "link": "https://www.example.com/python-tutorial",
            "snippet": "A comprehensive guide to learning Python programming from scratch. Perfect for beginners."
        },
        {
            "position": 2,
            "title": "Python Beginner Course - Coursera",
            "link": "https://www.coursera.org/learn/python",
            "snippet": "Start learning Python with this beginner-friendly course. No prior experience required."
        }
    ]
}


@pytest.fixture
def search_service():
    """Create a search service instance for testing."""
    return SearchService(provider_name="serpapi", api_key="test_key")


class TestSearchService:
    """Test case for the SearchService class."""

    def test_resource_creation(self):
        """Test that Resource objects are created correctly."""
        # Create a resource
        resource = Resource(
            title="Python Tutorial",
            url="https://example.com/python",
            description="Learn Python programming",
            resource_type=ResourceType.TUTORIAL,
            source="test",
            relevance_score=0.8,
            metadata={"test": "value"}
        )
        
        # Check resource properties
        assert resource.title == "Python Tutorial"
        assert resource.url == "https://example.com/python"
        assert resource.description == "Learn Python programming"
        assert resource.resource_type == ResourceType.TUTORIAL
        assert resource.source == "test"
        assert resource.relevance_score == 0.8
        assert resource.metadata == {"test": "value"}
        
        # Test to_dict method
        resource_dict = resource.to_dict()
        assert resource_dict["title"] == "Python Tutorial"
        assert resource_dict["url"] == "https://example.com/python"
        assert resource_dict["description"] == "Learn Python programming"
        assert resource_dict["resource_type"] == ResourceType.TUTORIAL
        assert resource_dict["source"] == "test"
        assert resource_dict["relevance_score"] == 0.8
        assert resource_dict["metadata"] == {"test": "value"}

    def test_query_generation(self, search_service):
        """Test query generation for different skills and proficiency levels."""
        # Test basic query
        query = search_service._generate_query("Python", "beginner")
        assert "Python" in query
        assert "beginner" in query
        
        # Test with job role
        query = search_service._generate_query("Python", "intermediate", "Data Scientist")
        assert "Python" in query
        assert "intermediate" in query
        assert "Data Scientist" in query
        
        # Test advanced level
        query = search_service._generate_query("Machine Learning", "advanced")
        assert "Machine Learning" in query
        assert "advanced" in query

    def test_resource_classification(self, search_service):
        """Test resource type classification based on title, URL, and description."""
        # Test course detection
        resource_type = search_service._classify_resource_type(
            "Python Programming Course", 
            "https://www.coursera.org/learn/python", 
            "Learn Python programming"
        )
        assert resource_type == ResourceType.COURSE
        
        # Test video detection
        resource_type = search_service._classify_resource_type(
            "Python Tutorial Video", 
            "https://www.youtube.com/watch?v=123456", 
            "Watch this tutorial"
        )
        assert resource_type == ResourceType.VIDEO
        
        # Test documentation detection
        resource_type = search_service._classify_resource_type(
            "Python Documentation", 
            "https://docs.python.org/3/", 
            "Official Python documentation"
        )
        assert resource_type == ResourceType.DOCUMENTATION
        
        # Test article detection (default)
        resource_type = search_service._classify_resource_type(
            "Python Tips and Tricks", 
            "https://blog.example.com/python-tips", 
            "Useful Python tips"
        )
        assert resource_type == ResourceType.ARTICLE

    def test_relevance_calculation(self, search_service):
        """Test relevance score calculation."""
        # High relevance (skill in title, URL, description)
        score = search_service._calculate_relevance(
            "Learn Python Programming",
            "https://example.com/python-tutorial",
            "Comprehensive Python tutorial for beginners",
            "python",
            "beginner"
        )
        assert score > 0.7
        
        # Medium relevance (skill in title only)
        score = search_service._calculate_relevance(
            "Learn Python Programming",
            "https://example.com/tutorial",
            "Comprehensive programming tutorial",
            "python",
            "beginner"
        )
        assert 0.3 < score < 0.8
        
        # Low relevance (skill not prominent)
        score = search_service._calculate_relevance(
            "Programming Basics",
            "https://example.com/tutorial",
            "Various programming languages including Python",
            "python",
            "beginner"
        )
        assert score < 0.3

    @patch('httpx.AsyncClient.get')
    async def test_serpapi_search(self, mock_get, search_service):
        """Test SerpAPI search functionality."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = SERPAPI_SAMPLE_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Replace the provider with a mocked one
        search_service.provider = SerpApiProvider(api_key="test_key")
        
        # Call the search method
        results = await search_service.provider.search("python beginner tutorial")
        
        # Verify the results
        assert "organic_results" in results
        assert len(results["organic_results"]) == 2
        assert "Python" in results["organic_results"][0]["title"]

    @patch('httpx.AsyncClient.post')
    async def test_serper_search(self, mock_post, search_service):
        """Test Serper.dev search functionality."""
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = SERPER_SAMPLE_RESPONSE
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Replace the provider with a mocked one
        search_service.provider = SerperProvider(api_key="test_key")
        
        # Call the search method
        results = await search_service.provider.search("python beginner tutorial")
        
        # Verify the results
        assert "organic" in results
        assert len(results["organic"]) == 2
        assert "Python" in results["organic"][0]["title"]

    @patch('backend.services.search_service.SerpApiProvider.search')
    async def test_search_resources(self, mock_search, search_service):
        """Test the search_resources method."""
        # Configure the mock
        mock_search.return_value = SERPAPI_SAMPLE_RESPONSE
        
        # Call the search_resources method
        resources = await search_service.search_resources(
            skill="python",
            proficiency_level="beginner"
        )
        
        # Verify the results
        assert len(resources) == 2
        assert resources[0].title == "Learn Python Programming - Beginner's Guide"
        assert resources[0].url == "https://www.example.com/python-tutorial"
        assert resources[0].relevance_score > 0
        
    def test_cache_functionality(self, search_service):
        """Test the caching functionality."""
        # Add some test data to the cache
        test_resources = [
            Resource(
                title="Test Resource",
                url="https://example.com",
                description="Test description",
                resource_type=ResourceType.ARTICLE,
                source="test",
                relevance_score=0.8
            )
        ]
        
        # Add to cache
        cache_key = "python_beginner_10"
        search_service._search_cache[cache_key] = test_resources
        search_service._search_cache_timestamps[cache_key] = datetime.utcnow()
        
        # Verify cache hit
        assert cache_key in search_service._search_cache
        
        # Test cache clearing
        search_service.clear_cache()
        assert cache_key not in search_service._search_cache
        assert cache_key not in search_service._search_cache_timestamps

    def test_fallback_resources(self, search_service):
        """Test fallback resource generation."""
        # Get fallback resources
        resources = search_service._get_fallback_resources("python", "beginner")
        
        # Verify the results
        assert len(resources) > 0
        assert all(isinstance(r, Resource) for r in resources)
        assert "python" in resources[0].title.lower()
        
        # Check that URLs are formatted correctly
        assert all(r.url.startswith("https://") for r in resources)


# Run asyncio tests
@pytest.mark.asyncio
async def test_async_search_wrapper():
    """Test async search functionality with both providers."""
    # Create a service with mocked providers
    with patch('backend.services.search_service.SerpApiProvider.search') as mock_serpapi:
        mock_serpapi.return_value = SERPAPI_SAMPLE_RESPONSE
        
        service = SearchService(provider_name="serpapi")
        
        # Call the search_resources method
        resources = await service.search_resources(
            skill="python",
            proficiency_level="beginner"
        )
        
        assert len(resources) > 0
        assert all(isinstance(r, Resource) for r in resources)
        
    with patch('backend.services.search_service.SerperProvider.search') as mock_serper:
        mock_serper.return_value = SERPER_SAMPLE_RESPONSE
        
        service = SearchService(provider_name="serper")
        
        # Call the search_resources method
        resources = await service.search_resources(
            skill="python",
            proficiency_level="beginner"
        )
        
        assert len(resources) > 0
        assert all(isinstance(r, Resource) for r in resources) 