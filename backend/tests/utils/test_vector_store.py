"""
Tests for the vector store module.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from backend.utils.vector_store import VectorStore


@pytest.fixture
def vector_store():
    """Create a vector store instance for testing."""
    return VectorStore()


@pytest.fixture
def sample_texts():
    """Create sample texts for testing."""
    return [
        "This is a test document.",
        "Another test document.",
        "A third test document."
    ]


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return [
        {"source": "test1", "id": 1},
        {"source": "test2", "id": 2},
        {"source": "test3", "id": 3}
    ]


class TestVectorStore:
    """Tests for the VectorStore class."""
    
    @patch('backend.utils.vector_store.GoogleGenerativeAI')
    def test_initialization(self, mock_google_ai):
        """Test that vector store initializes properly."""
        store = VectorStore()
        assert store.model is not None
        assert store.index is not None
        assert store.metadata == []
    
    @patch('backend.utils.vector_store.GoogleGenerativeAI')
    def test_generate_embeddings(self, mock_google_ai, vector_store, sample_texts):
        """Test embedding generation."""
        # Mock the embedding model response
        mock_embeddings = [np.random.rand(768) for _ in sample_texts]
        vector_store.model.get_embeddings = MagicMock(return_value=mock_embeddings)
        
        # Generate embeddings
        embeddings = vector_store.generate_embeddings(sample_texts)
        
        # Verify embeddings
        assert len(embeddings) == len(sample_texts)
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        assert all(emb.shape == (768,) for emb in embeddings)
        
        # Verify model was called correctly
        vector_store.model.get_embeddings.assert_called_once_with(sample_texts)
    
    def test_store_embeddings(self, vector_store, sample_texts, sample_metadata):
        """Test storing embeddings with metadata."""
        # Mock embedding generation
        mock_embeddings = [np.random.rand(768) for _ in sample_texts]
        vector_store.generate_embeddings = MagicMock(return_value=mock_embeddings)
        
        # Store embeddings
        vector_store.store_embeddings(sample_texts, sample_metadata)
        
        # Verify metadata was stored
        assert len(vector_store.metadata) == len(sample_texts)
        assert vector_store.metadata == sample_metadata
        
        # Verify index was updated
        assert vector_store.index.ntotal == len(sample_texts)
    
    def test_retrieve_embeddings(self, vector_store, sample_texts, sample_metadata):
        """Test retrieving similar embeddings."""
        # Mock embedding generation and storage
        mock_embeddings = [np.random.rand(768) for _ in sample_texts]
        vector_store.generate_embeddings = MagicMock(return_value=mock_embeddings)
        vector_store.store_embeddings(sample_texts, sample_metadata)
        
        # Create a query embedding
        query_embedding = np.random.rand(768)
        
        # Retrieve similar embeddings
        k = 2
        distances, indices = vector_store.retrieve_embeddings(query_embedding, k)
        
        # Verify results
        assert len(distances) == k
        assert len(indices) == k
        assert all(isinstance(d, float) for d in distances)
        assert all(isinstance(i, int) for i in indices)
        assert all(0 <= i < len(sample_texts) for i in indices)
    
    def test_get_metadata(self, vector_store, sample_texts, sample_metadata):
        """Test retrieving metadata for indices."""
        # Store embeddings with metadata
        mock_embeddings = [np.random.rand(768) for _ in sample_texts]
        vector_store.generate_embeddings = MagicMock(return_value=mock_embeddings)
        vector_store.store_embeddings(sample_texts, sample_metadata)
        
        # Get metadata for indices
        indices = [0, 1]
        retrieved_metadata = vector_store.get_metadata(indices)
        
        # Verify metadata
        assert len(retrieved_metadata) == len(indices)
        assert retrieved_metadata == [sample_metadata[i] for i in indices]
    
    def test_save_and_load(self, vector_store, sample_texts, sample_metadata, tmp_path):
        """Test saving and loading the vector store."""
        # Store some embeddings
        mock_embeddings = [np.random.rand(768) for _ in sample_texts]
        vector_store.generate_embeddings = MagicMock(return_value=mock_embeddings)
        vector_store.store_embeddings(sample_texts, sample_metadata)
        
        # Save the store
        save_path = tmp_path / "vector_store"
        vector_store.save(save_path)
        
        # Create a new store and load the saved one
        new_store = VectorStore()
        new_store.load(save_path)
        
        # Verify the loaded store
        assert len(new_store.metadata) == len(sample_metadata)
        assert new_store.metadata == sample_metadata
        assert new_store.index.ntotal == len(sample_texts)
    
    def test_clear(self, vector_store, sample_texts, sample_metadata):
        """Test clearing the vector store."""
        # Store some embeddings
        mock_embeddings = [np.random.rand(768) for _ in sample_texts]
        vector_store.generate_embeddings = MagicMock(return_value=mock_embeddings)
        vector_store.store_embeddings(sample_texts, sample_metadata)
        
        # Clear the store
        vector_store.clear()
        
        # Verify store is empty
        assert len(vector_store.metadata) == 0
        assert vector_store.index.ntotal == 0


if __name__ == "__main__":
    pytest.main(["-v"]) 