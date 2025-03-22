"""
Vector store module for embedding storage and retrieval.
Provides utilities for adding, searching, and managing vectors using FAISS.
"""

import os
import json
import pickle
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector store for storing and retrieving embeddings using FAISS.
    
    This class provides a simple interface to:
    - Generate embeddings from text
    - Store embeddings in a FAISS index
    - Search for similar embeddings
    - Associate metadata with embeddings
    """
    
    def __init__(
        self,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        index_dir: str = "./data/vector_store",
        dimension: int = 384,  # Default for all-MiniLM-L6-v2
        batch_size: int = 16,
        use_gpu: bool = False
    ):
        """
        Initialize the vector store.
        
        Args:
            embedding_model_name: Name of the sentence-transformers model to use
            index_dir: Directory to store the FAISS index
            dimension: Dimension of the embeddings (384 for all-MiniLM-L6-v2)
            batch_size: Batch size for embedding generation
            use_gpu: Whether to use GPU for embedding generation and FAISS
        """
        self.embedding_model_name = embedding_model_name
        self.index_dir = Path(index_dir)
        self.dimension = dimension
        self.batch_size = batch_size
        self.use_gpu = use_gpu
        
        # Create index directory if it doesn't exist
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Initialize FAISS index
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        
        # Load existing index if available, otherwise create new
        self._load_or_create_index()
    
    def _load_or_create_index(self) -> None:
        """
        Load existing index or create a new one if it doesn't exist.
        """
        index_path = self.index_dir / f"index_{self.embedding_model_name.replace('/', '_')}.faiss"
        metadata_path = self.index_dir / f"metadata_{self.embedding_model_name.replace('/', '_')}.json"
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            try:
                logger.info(f"Loading existing index from {index_path}")
                self.index = faiss.read_index(str(index_path))
                
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                    
                logger.info(f"Loaded index with {self.index.ntotal} vectors and {len(self.metadata)} metadata entries")
            except Exception as e:
                logger.error(f"Error loading index: {e}")
                self._create_new_index()
        else:
            logger.info("No existing index found, creating new one")
            self._create_new_index()
    
    def _create_new_index(self) -> None:
        """
        Create a new FAISS index.
        """
        # Create a flat L2 index for exact search
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        
        # Save the empty index
        self._save_index()
    
    def _save_index(self) -> None:
        """
        Save the FAISS index and metadata to disk.
        """
        index_path = self.index_dir / f"index_{self.embedding_model_name.replace('/', '_')}.faiss"
        metadata_path = self.index_dir / f"metadata_{self.embedding_model_name.replace('/', '_')}.json"
        
        try:
            # Save the index
            faiss.write_index(self.index, str(index_path))
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f)
                
            logger.info(f"Saved index with {self.index.ntotal} vectors to {index_path}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector
        """
        return self.embedding_model.encode(text, show_progress_bar=False)
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            Array of embedding vectors
        """
        return self.embedding_model.encode(
            texts, 
            batch_size=self.batch_size, 
            show_progress_bar=True
        )
    
    def add_texts(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[int]:
        """
        Add texts and their metadata to the vector store.
        
        Args:
            texts: List of texts to add
            metadatas: Optional list of metadata dictionaries
            
        Returns:
            List of IDs for the added vectors
        """
        if not texts:
            return []
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Add to FAISS index
        start_idx = self.index.ntotal
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Add metadata
        if metadatas:
            for i, metadata in enumerate(metadatas):
                # Add timestamp and ID
                metadata_with_id = metadata.copy()
                metadata_with_id["id"] = start_idx + i
                metadata_with_id["timestamp"] = datetime.utcnow().isoformat()
                self.metadata.append(metadata_with_id)
        else:
            # Create simple metadata with IDs
            for i in range(len(texts)):
                self.metadata.append({
                    "id": start_idx + i,
                    "text": texts[i][:100] + "..." if len(texts[i]) > 100 else texts[i],
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Save the updated index
        self._save_index()
        
        # Return IDs
        return list(range(start_idx, start_idx + len(texts)))
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar texts.
        
        Args:
            query: Query text
            k: Number of results to return
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of results with similarity scores and metadata
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Search in FAISS
        return self.similarity_search_by_vector(
            query_embedding, 
            k=k,
            include_metadata=include_metadata
        )
    
    def similarity_search_by_vector(
        self, 
        embedding: np.ndarray, 
        k: int = 5,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings by vector.
        
        Args:
            embedding: Query embedding
            k: Number of results to return
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of results with similarity scores and metadata
        """
        if self.index.ntotal == 0:
            return []
        
        # Ensure k doesn't exceed the number of items
        k = min(k, self.index.ntotal)
        
        # Reshape if needed
        embedding_np = np.array([embedding]).astype('float32')
        
        # Search
        distances, indices = self.index.search(embedding_np, k)
        
        # Format results
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            distance = distances[0][i]
            
            result = {
                "id": int(idx),
                "score": float(1.0 - distance / 100.0),  # Convert distance to similarity score
            }
            
            # Add metadata if available and requested
            if include_metadata and idx < len(self.metadata):
                result["metadata"] = self.metadata[idx]
            
            results.append(result)
        
        return results
    
    def delete(self, ids: List[int]) -> None:
        """
        Delete vectors by ID.
        
        Note: FAISS requires rebuilding the index for deletion, which can be expensive.
        For simplicity, we just mark metadata as deleted for now.
        
        Args:
            ids: List of IDs to delete
        """
        if not self.index or self.index.ntotal == 0:
            return
        
        # Mark metadata as deleted
        for idx in ids:
            if 0 <= idx < len(self.metadata):
                self.metadata[idx]["deleted"] = True
                self.metadata[idx]["deleted_at"] = datetime.utcnow().isoformat()
        
        # Save the updated index
        self._save_index()
        
        # TODO: Implement actual deletion by rebuilding the index
        # This would involve:
        # 1. Creating a new index
        # 2. Collecting all non-deleted embeddings
        # 3. Adding them to the new index
        # 4. Replacing the old index with the new one
        
        logger.info(f"Marked {len(ids)} vectors as deleted")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "total_metadata": len(self.metadata),
            "deleted_vectors": sum(1 for m in self.metadata if m.get("deleted", False)),
            "embedding_model": self.embedding_model_name,
            "dimension": self.dimension,
            "index_type": str(type(self.index).__name__) if self.index else None,
            "memory_usage_mb": self.index.ntotal * self.dimension * 4 / (1024 * 1024) if self.index else 0
        } 