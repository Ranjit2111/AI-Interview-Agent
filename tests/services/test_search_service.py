import pytest
import httpx
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from backend.services.search_service import SearchService, Resource, ResourceType, SerperProvider

# Configure logging for tests
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def search_service_instance():
    logger.debug("Creating SearchService instance for test")
    # We will mock the provider within tests where necessary
    return SearchService(logger=logger)

@pytest.mark.asyncio
async def test_search_service_initialization(search_service_instance):
    logger.info("Running test_search_service_initialization")
    assert search_service_instance is not None
    assert isinstance(search_service_instance.provider, SerperProvider)
    logger.info("test_search_service_initialization PASSED")

@pytest.mark.asyncio
async def test_search_resources_success_and_caching(search_service_instance):
    logger.info("Running test_search_resources_success_and_caching")
    sample_serper_response = {
        "organic": [
            {
                "title": "Learn Python Basics",
                "link": "https://example.com/python-basics",
                "snippet": "A beginner's guide to Python programming.",
                "position": 1
            },
            {
                "title": "Advanced Python Course",
                "link": "https://example.com/python-advanced",
                "snippet": "Deep dive into advanced Python topics. Python expert course.",
                "position": 2
            },
            {
                "title": "YouTube Python Tutorial",
                "link": "https://youtube.com/python-tutorial",
                "snippet": "Watch this video to learn python",
                "position": 3
            }
        ]
    }

    # Patch the SerperProvider's search method
    with patch.object(SerperProvider, 'search', new_callable=AsyncMock) as mock_serper_search:
        mock_serper_search.return_value = sample_serper_response
        search_service_instance.provider = SerperProvider() # Re-assign to ensure our mock is on this instance if it was already created differently

        # First call - should call Serper API
        logger.debug("First call to search_resources")
        resources = await search_service_instance.search_resources("Python", "beginner", "Software Engineer")
        
        assert len(resources) == 3
        assert mock_serper_search.call_count == 1
        
        # Check processing
        assert resources[0].title == "Learn Python Basics"
        assert resources[0].url == "https://example.com/python-basics"
        assert resources[0].resource_type == ResourceType.ARTICLE # Example, depends on actual classification
        assert resources[0].description == "A beginner's guide to Python programming."
        assert resources[0].source == "serper"
        assert resources[0].relevance_score > 0 # Should have some relevance

        assert resources[1].title == "Advanced Python Course"
        assert resources[1].resource_type == ResourceType.COURSE 
        
        assert resources[2].title == "YouTube Python Tutorial"
        assert resources[2].resource_type == ResourceType.VIDEO

        # Second call with same parameters - should use cache
        logger.debug("Second call to search_resources (cached)")
        cached_resources = await search_service_instance.search_resources("Python", "beginner", "Software Engineer")
        assert len(cached_resources) == 3
        assert mock_serper_search.call_count == 1 # Should not be called again
        assert cached_resources[0].title == "Learn Python Basics" # Verify content consistency

        # Third call with different parameters - should call Serper API again
        logger.debug("Third call to search_resources (new query)")
        await search_service_instance.search_resources("Java", "intermediate", "Backend Developer")
        assert mock_serper_search.call_count == 2

    logger.info("test_search_resources_success_and_caching PASSED")

@pytest.mark.asyncio
async def test_search_resources_serper_failure_fallback(search_service_instance):
    logger.info("Running test_search_resources_serper_failure_fallback")
    
    # Patch the SerperProvider's search method to raise an error
    with patch.object(SerperProvider, 'search', new_callable=AsyncMock) as mock_serper_search:
        mock_serper_search.side_effect = httpx.HTTPError("Simulated API error")
        search_service_instance.provider = SerperProvider()

        # Patch _get_fallback_resources to monitor its call and control its output
        with patch.object(SearchService, '_get_fallback_resources', autospec=True) as mock_get_fallback:
            # Ensure the mock returns a list of Resource objects as the original would
            fallback_resource_list = [
                Resource(title="Fallback Python", url="fallback.com/python", description="Fallback", resource_type=ResourceType.ARTICLE, source="fallback")
            ]
            # Since _get_fallback_resources is a method of the instance, we set the return_value on the instance's method
            search_service_instance._get_fallback_resources = MagicMock(return_value=fallback_resource_list)


            logger.debug("Calling search_resources expecting Serper failure and fallback")
            resources = await search_service_instance.search_resources("Python", "beginner")
            
            assert mock_serper_search.call_count == 1 # Serper search was attempted
            search_service_instance._get_fallback_resources.assert_called_once() # Fallback was called
            
            assert len(resources) == 1
            assert resources[0].title == "Fallback Python"
            assert resources[0].source == "fallback"

    logger.info("test_search_resources_serper_failure_fallback PASSED")

def test_classify_resource_type_direct(search_service_instance):
    logger.info("Running test_classify_resource_type_direct")
    classify_method = search_service_instance._classify_resource_type
    
    # Test cases: (title, url, description, expected_type)
    test_cases = [
        ("Python Course", "udemy.com/python-course", "Learn python programming", ResourceType.COURSE),
        ("Watch Python Video", "youtube.com/watch?v=123", "Python tutorial video", ResourceType.VIDEO),
        ("Python Docs", "docs.python.org/3/", "Official Python documentation", ResourceType.DOCUMENTATION),
        ("Python Tutorial Guide", "example.com/python-tutorial", "Step-by-step python guide", ResourceType.TUTORIAL),
        ("Python Community Forum", "forum.python.org", "Discuss Python", ResourceType.COMMUNITY),
        ("Python Book Review", "goodreads.com/book/python", "Review of a Python book", ResourceType.BOOK),
        ("Simple Python Article", "blog.com/python-article", "An article about python", ResourceType.ARTICLE),
    ]
    
    for title, url, description, expected_type in test_cases:
        logger.debug(f"Classifying: {title}, {url}")
        assert classify_method(title, url, description) == expected_type, f"Failed for {title}"
    logger.info("test_classify_resource_type_direct PASSED")

# It's good practice to also test helper methods like _generate_query and _calculate_relevance
# For brevity here, focusing on core changes, but they should be tested.

@pytest.mark.asyncio
async def test_clear_cache(search_service_instance):
    logger.info("Running test_clear_cache")
    sample_serper_response = {"organic": [{"title": "Cache Test", "link": "cache.com", "snippet": "Test cache"}]}
    
    with patch.object(SerperProvider, 'search', new_callable=AsyncMock, return_value=sample_serper_response) as mock_serper_search:
        search_service_instance.provider = SerperProvider()

        await search_service_instance.search_resources("CacheSkill", "beginner")
        assert mock_serper_search.call_count == 1

        await search_service_instance.search_resources("CacheSkill", "beginner") # Should use cache
        assert mock_serper_search.call_count == 1
        
        search_service_instance.clear_cache()
        logger.debug("Cache cleared")
        
        await search_service_instance.search_resources("CacheSkill", "beginner") # Should call API again
        assert mock_serper_search.call_count == 2
        
    logger.info("test_clear_cache PASSED") 