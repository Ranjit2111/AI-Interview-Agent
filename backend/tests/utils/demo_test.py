"""
Demo test file to showcase mock services usage.
This file demonstrates how to use mock services for testing.
"""

import pytest
from unittest.mock import patch
import numpy as np
from backend.tests.utils.mock_services import MockGeminiAPI, MockSentenceTransformer, MockFAISS, MockWebSearch

# Test data
TEST_TEXT = "This is a test text for demonstration"


def test_mock_gemini_api():
    """
    Test demonstrating how to use MockGeminiAPI.
    """
    # Create mock with predefined responses
    mock_api = MockGeminiAPI({
        "Tell me about Python": "Python is a popular programming language.",
        "What is an interview": "An interview is a conversation where a person is asked questions."
    })
    
    # Test predefined response
    response = mock_api.generate_content("Tell me about Python")
    assert "Python is a popular programming language" in response["candidates"][0]["content"]["parts"][0]["text"]
    
    # Test default response for undefined input
    response = mock_api.generate_content("Tell me about JavaScript")
    assert "This is a mock response for:" in response["candidates"][0]["content"]["parts"][0]["text"]
    
    # Check call history
    assert mock_api.get_call_count() == 2
    assert mock_api.call_history[0]["prompt"] == "Tell me about Python"
    
    # Reset call history
    mock_api.reset()
    assert mock_api.get_call_count() == 0


def test_mock_sentence_transformer():
    """
    Test demonstrating how to use MockSentenceTransformer.
    """
    # Create mock with custom dimension
    mock_transformer = MockSentenceTransformer(dimension=512)
    
    # Test single text encoding
    embedding = mock_transformer.encode(TEST_TEXT)
    assert embedding.shape == (512,)
    assert embedding.dtype == np.float32
    
    # Test batch encoding
    batch_embeddings = mock_transformer.encode([TEST_TEXT, "Another text"])
    assert batch_embeddings.shape == (2, 512)
    
    # Check deterministic behavior (same input should give same embedding)
    embedding2 = mock_transformer.encode(TEST_TEXT)
    assert np.array_equal(embedding, embedding2)
    
    # Check call history
    assert mock_transformer.get_call_count() == 3


def test_mock_faiss():
    """
    Test demonstrating how to use MockFAISS.
    """
    # Create mock index
    index = MockFAISS.IndexFlatL2(128)
    
    # Create test vectors
    vectors = np.random.randn(5, 128).astype(np.float32)
    
    # Add vectors to index
    index.add(vectors)
    assert index.ntotal == 5
    
    # Search nearest neighbors
    query = np.random.randn(1, 128).astype(np.float32)
    distances, indices = index.search(query, k=3)
    
    # Check search results
    assert distances.shape == (1, 3)
    assert indices.shape == (1, 3)
    assert all(idx < 5 for idx in indices[0])
    
    # Test read/write functions
    mock_index = MockFAISS.read_index("dummy_path.index")
    assert isinstance(mock_index, MockFAISS.IndexFlatL2)
    
    # Writing should not raise errors
    MockFAISS.write_index(index, "dummy_path.index")


def test_mock_web_search():
    """
    Test demonstrating how to use MockWebSearch.
    """
    # Create mock with custom results
    custom_results = {
        "python programming": [
            {
                "title": "Learn Python Programming",
                "link": "https://example.com/python",
                "snippet": "Python tutorials for beginners and experts."
            }
        ]
    }
    mock_search = MockWebSearch(results=custom_results)
    
    # Test with predefined query
    results = mock_search.search("python programming")
    assert results["organic"][0]["title"] == "Learn Python Programming"
    
    # Test with undefined query
    results = mock_search.search("javascript programming")
    assert "Mock Result" in results["organic"][0]["title"]
    assert "javascript programming" in results["organic"][0]["link"]
    
    # Check call history
    assert mock_search.get_call_count() == 2
    mock_search.reset()
    assert mock_search.get_call_count() == 0


@patch("backend.tests.utils.mock_services.MockGeminiAPI")
def test_with_patch(mock_gemini_api_class):
    """
    Test demonstrating how to use patch to inject mock services.
    """
    # Set up the mock
    mock_instance = MockGeminiAPI()
    mock_gemini_api_class.return_value = mock_instance
    
    # In real code, this would be importing and using GeminiAPI
    # but here we're directly using the mocked version
    api = mock_gemini_api_class()
    api.generate_content("Hello")
    
    # Verify mock was called
    assert api.get_call_count() == 1


if __name__ == "__main__":
    # Run the tests directly
    pytest.main(["-v", __file__]) 