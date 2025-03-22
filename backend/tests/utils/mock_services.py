"""
Mock services for external APIs used in testing.
This module provides mock implementations of external services to facilitate testing without real API calls.
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional, Union
from unittest.mock import MagicMock

class MockGeminiAPI:
    """
    Mock implementation of the Google Gemini API for testing.
    """
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """
        Initialize the mock Gemini API.
        
        Args:
            responses: Optional dictionary mapping input patterns to predefined responses
        """
        self.responses = responses or {}
        self.call_history = []
        
    def generate_content(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Mock the generate_content method of the Gemini API.
        
        Args:
            prompt: The prompt text
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing the response
        """
        self.call_history.append({
            "prompt": prompt,
            "params": kwargs
        })
        
        # Match against predefined responses if available
        for pattern, response in self.responses.items():
            if pattern in prompt:
                return {"candidates": [{"content": {"parts": [{"text": response}]}}]}
        
        # Default response based on input
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": f"This is a mock response for: {prompt[:50]}..."
                            }
                        ]
                    }
                }
            ]
        }
    
    def get_call_count(self) -> int:
        """
        Get the number of calls made to the API.
        
        Returns:
            Number of calls
        """
        return len(self.call_history)
    
    def reset(self) -> None:
        """
        Reset the call history.
        """
        self.call_history = []


class MockSentenceTransformer:
    """
    Mock implementation of the SentenceTransformer for testing.
    """
    
    def __init__(self, dimension: int = 384):
        """
        Initialize the mock SentenceTransformer.
        
        Args:
            dimension: Dimension of the embeddings
        """
        self.dimension = dimension
        self.call_history = []
    
    def encode(self, texts: Union[str, List[str]], **kwargs) -> np.ndarray:
        """
        Mock the encode method of SentenceTransformer.
        
        Args:
            texts: Text or list of texts to encode
            **kwargs: Additional parameters
            
        Returns:
            Numpy array of embeddings
        """
        self.call_history.append({
            "texts": texts,
            "params": kwargs
        })
        
        if isinstance(texts, str):
            # Generate a deterministic embedding based on the hash of the text
            seed = sum(ord(c) for c in texts)
            np.random.seed(seed)
            return np.random.randn(self.dimension).astype(np.float32)
        else:
            # Generate embeddings for a list of texts
            embeddings = []
            for text in texts:
                seed = sum(ord(c) for c in text)
                np.random.seed(seed)
                embeddings.append(np.random.randn(self.dimension).astype(np.float32))
            return np.array(embeddings)
    
    def get_call_count(self) -> int:
        """
        Get the number of calls made to the encoder.
        
        Returns:
            Number of calls
        """
        return len(self.call_history)
    
    def reset(self) -> None:
        """
        Reset the call history.
        """
        self.call_history = []


class MockFAISS:
    """
    Mock implementation of FAISS for testing.
    """
    
    class IndexFlatL2:
        """
        Mock implementation of FAISS IndexFlatL2.
        """
        
        def __init__(self, dimension: int):
            """
            Initialize the mock FAISS IndexFlatL2.
            
            Args:
                dimension: Dimension of the index
            """
            self.dimension = dimension
            self.vectors = []
            self.ntotal = 0
        
        def add(self, vectors: np.ndarray) -> None:
            """
            Mock the add method of FAISS IndexFlatL2.
            
            Args:
                vectors: Vectors to add
            """
            if len(vectors.shape) == 1:
                vectors = vectors.reshape(1, -1)
            
            for vector in vectors:
                self.vectors.append(vector)
            
            self.ntotal = len(self.vectors)
        
        def search(self, query_vectors: np.ndarray, k: int) -> tuple:
            """
            Mock the search method of FAISS IndexFlatL2.
            
            Args:
                query_vectors: Query vectors
                k: Number of results
                
            Returns:
                Tuple of (distances, indices)
            """
            if len(query_vectors.shape) == 1:
                query_vectors = query_vectors.reshape(1, -1)
            
            distances = []
            indices = []
            
            for query in query_vectors:
                # Calculate distances (simplified for mock)
                dist = []
                for i, vector in enumerate(self.vectors):
                    # L2 distance approximation
                    d = np.sum((query - vector) ** 2)
                    dist.append((d, i))
                
                # Sort by distance
                dist.sort()
                
                # Take top k
                top_k = dist[:min(k, len(dist))]
                
                # Split into distances and indices
                d, idx = zip(*top_k) if top_k else ([], [])
                
                distances.append(d)
                indices.append(idx)
            
            return np.array(distances), np.array(indices)
    
    @staticmethod
    def read_index(filename: str):
        """
        Mock the read_index function of FAISS.
        
        Args:
            filename: Filename to read
            
        Returns:
            A mock index
        """
        return MockFAISS.IndexFlatL2(384)
    
    @staticmethod
    def write_index(index, filename: str) -> None:
        """
        Mock the write_index function of FAISS.
        
        Args:
            index: Index to write
            filename: Filename to write to
        """
        pass


class MockWebSearch:
    """
    Mock implementation of web search API for testing.
    """
    
    def __init__(self, results: Optional[Dict[str, List[Dict[str, str]]]] = None):
        """
        Initialize the mock web search API.
        
        Args:
            results: Optional dictionary mapping queries to predefined search results
        """
        self.results = results or {}
        self.call_history = []
    
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Mock the search method of web search API.
        
        Args:
            query: The search query
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing search results
        """
        self.call_history.append({
            "query": query,
            "params": kwargs
        })
        
        # Return predefined results if available
        if query in self.results:
            return {
                "organic": self.results[query],
                "query": query
            }
        
        # Default search results
        return {
            "organic": [
                {
                    "title": f"Mock Result 1 for {query}",
                    "link": f"https://example.com/result1?q={query}",
                    "snippet": f"This is a mock search result for the query: {query}. It contains relevant information."
                },
                {
                    "title": f"Mock Result 2 for {query}",
                    "link": f"https://example.com/result2?q={query}",
                    "snippet": f"Another mock search result with different information about {query}."
                }
            ],
            "query": query
        }
    
    def get_call_count(self) -> int:
        """
        Get the number of calls made to the search API.
        
        Returns:
            Number of calls
        """
        return len(self.call_history)
    
    def reset(self) -> None:
        """
        Reset the call history.
        """
        self.call_history = []


# Mock API key for testing
MOCK_API_KEY = "mock_api_key_for_testing_only"

# Create a patch dict for common external dependencies
mock_patches = {
    "langchain_google_genai.ChatGoogleGenerativeAI": MagicMock(),
    "sentence_transformers.SentenceTransformer": MockSentenceTransformer,
    "faiss": MockFAISS
} 