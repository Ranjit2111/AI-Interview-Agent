"""
Vector store module for embedding storage and retrieval.
Provides utilities for adding, searching, and managing vectors using FAISS.
"""

import os
import json
import pickle
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime
import logging
from pathlib import Path
import uuid

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
    - Support batch processing for better performance
    - Handle namespaces for organizing embeddings
    """
    
    def __init__(
        self,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        index_dir: str = "./data/vector_store",
        dimension: int = 384,  # Default for all-MiniLM-L6-v2
        batch_size: int = 16,
        use_gpu: bool = False,
        index_type: str = "flat"  # 'flat', 'ivf', 'hnsw'
    ):
        """
        Initialize the vector store.
        
        Args:
            embedding_model_name: Name of the sentence-transformers model to use
            index_dir: Directory to store the FAISS index
            dimension: Dimension of the embeddings (384 for all-MiniLM-L6-v2)
            batch_size: Batch size for embedding generation
            use_gpu: Whether to use GPU for embedding generation and FAISS
            index_type: Type of FAISS index to use ('flat', 'ivf', 'hnsw')
        """
        self.embedding_model_name = embedding_model_name
        self.index_dir = Path(index_dir)
        self.dimension = dimension
        self.batch_size = batch_size
        self.use_gpu = use_gpu
        self.index_type = index_type
        
        # Create index directory if it doesn't exist
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        # Initialize FAISS index
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        
        # Track namespaces for organizing embeddings
        self.namespaces = {}
        
        # Load existing index if available, otherwise create new
        self._load_or_create_index()
    
    def _load_or_create_index(self) -> None:
        """
        Load existing index or create a new one if it doesn't exist.
        """
        index_path = self.index_dir / f"index_{self.embedding_model_name.replace('/', '_')}.faiss"
        metadata_path = self.index_dir / f"metadata_{self.embedding_model_name.replace('/', '_')}.json"
        namespace_path = self.index_dir / f"namespaces_{self.embedding_model_name.replace('/', '_')}.json"
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            try:
                logger.info(f"Loading existing index from {index_path}")
                self.index = faiss.read_index(str(index_path))
                
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                
                # Load namespaces if available
                if os.path.exists(namespace_path):
                    with open(namespace_path, 'r') as f:
                        self.namespaces = json.load(f)
                    
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
        # Create the appropriate index based on type
        if self.index_type == 'flat':
            # Create a flat L2 index for exact search
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == 'ivf':
            # Create an IVF index for faster search (at the cost of some accuracy)
            # Requires training data, so we'll start with a flat index and convert later
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == 'hnsw':
            # Create an HNSW index for even faster search
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)  # 32 neighbors
        else:
            # Default to flat
            self.index = faiss.IndexFlatL2(self.dimension)
        
        self.metadata = []
        self.namespaces = {}
        
        # Save the empty index
        self._save_index()
    
    def _save_index(self) -> None:
        """
        Save the FAISS index and metadata to disk.
        """
        index_path = self.index_dir / f"index_{self.embedding_model_name.replace('/', '_')}.faiss"
        metadata_path = self.index_dir / f"metadata_{self.embedding_model_name.replace('/', '_')}.json"
        namespace_path = self.index_dir / f"namespaces_{self.embedding_model_name.replace('/', '_')}.json"
        
        try:
            # Save the index
            faiss.write_index(self.index, str(index_path))
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f)
            
            # Save namespaces
            with open(namespace_path, 'w') as f:
                json.dump(self.namespaces, f)
                
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
        metadatas: Optional[List[Dict[str, Any]]] = None,
        namespace: Optional[str] = None,
        batch_size: Optional[int] = None
    ) -> List[str]:
        """
        Add texts and their metadata to the vector store.
        
        Args:
            texts: List of texts to add
            metadatas: Optional list of metadata dictionaries
            namespace: Optional namespace to organize embeddings
            batch_size: Optional batch size for processing large amounts of text
            
        Returns:
            List of IDs for the added vectors
        """
        if not texts:
            return []
        
        # Use provided batch size or default
        batch_size = batch_size or self.batch_size
        
        # Process in batches if needed
        if len(texts) > batch_size:
            all_ids = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_metadatas = None
                if metadatas:
                    batch_metadatas = metadatas[i:i+batch_size]
                batch_ids = self._add_texts_batch(batch_texts, batch_metadatas, namespace)
                all_ids.extend(batch_ids)
            return all_ids
        else:
            return self._add_texts_batch(texts, metadatas, namespace)
    
    def _add_texts_batch(
        self, 
        texts: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        namespace: Optional[str] = None
    ) -> List[str]:
        """
        Add a batch of texts to the index.
        
        Args:
            texts: Batch of texts to add
            metadatas: Optional metadata for each text
            namespace: Optional namespace
            
        Returns:
            List of IDs for the added vectors
        """
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Add to FAISS index
        start_idx = self.index.ntotal
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Generate unique IDs for each vector
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # Add metadata
        for i in range(len(texts)):
            # Get or create metadata
            metadata_entry = {}
            if metadatas and i < len(metadatas):
                metadata_entry = metadatas[i].copy()
            
            # Add basic info
            metadata_entry["id"] = ids[i]
            metadata_entry["index"] = start_idx + i
            metadata_entry["text"] = texts[i][:100] + "..." if len(texts[i]) > 100 else texts[i]
            metadata_entry["timestamp"] = datetime.utcnow().isoformat()
            
            # Add namespace if provided
            if namespace:
                metadata_entry["namespace"] = namespace
                
                # Update namespace tracking
                if namespace not in self.namespaces:
                    self.namespaces[namespace] = []
                self.namespaces[namespace].append(start_idx + i)
            
            self.metadata.append(metadata_entry)
        
        # Save the updated index
        self._save_index()
        
        return ids
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        namespace: Optional[str] = None,
        include_metadata: bool = True,
        filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar texts.
        
        Args:
            query: Query text
            k: Number of results to return
            namespace: Optional namespace to search within
            include_metadata: Whether to include metadata in results
            filter_fn: Optional function to filter results
            
        Returns:
            List of results with similarity scores and metadata
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Search in FAISS
        return self.similarity_search_by_vector(
            query_embedding, 
            k=k,
            namespace=namespace,
            include_metadata=include_metadata,
            filter_fn=filter_fn
        )
    
    def similarity_search_by_vector(
        self, 
        embedding: np.ndarray, 
        k: int = 5,
        namespace: Optional[str] = None,
        include_metadata: bool = True,
        filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings by vector.
        
        Args:
            embedding: Query embedding
            k: Number of results to return
            namespace: Optional namespace to search within
            include_metadata: Whether to include metadata in results
            filter_fn: Optional function to filter results
            
        Returns:
            List of results with similarity scores and metadata
        """
        if self.index.ntotal == 0:
            return []
        
        # Ensure k doesn't exceed the number of items or get too small
        k = min(k, self.index.ntotal)
        k = max(k, 1)
        
        # If we're filtering by namespace or function, request more results
        final_k = k
        search_k = k
        if namespace or filter_fn:
            # Request more results to allow for filtering
            search_k = min(k * 10, self.index.ntotal)
        
        # Reshape if needed
        embedding_np = np.array([embedding]).astype('float32')
        
        # Search
        distances, indices = self.index.search(embedding_np, search_k)
        
        # Format and filter results
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            distance = distances[0][i]
            
            # Get metadata
            metadata_entry = self.metadata[idx] if idx < len(self.metadata) else {}
            
            # Filter by namespace if specified
            if namespace and metadata_entry.get("namespace") != namespace:
                continue
            
            # Apply custom filter if provided
            if filter_fn and not filter_fn(metadata_entry):
                continue
            
            # Skip deleted items
            if metadata_entry.get("deleted", False):
                continue
            
            # Create result entry
            result = {
                "id": metadata_entry.get("id", str(idx)),
                "score": float(1.0 - min(distance / 100.0, 0.99)),  # Convert distance to similarity score
                "text": metadata_entry.get("text", "")
            }
            
            # Add metadata if available and requested
            if include_metadata:
                result["metadata"] = metadata_entry
            
            results.append(result)
            
            # Stop if we have enough filtered results
            if len(results) >= final_k:
                break
        
        return results
    
    def batch_similarity_search(
        self,
        queries: List[str],
        k: int = 5,
        namespace: Optional[str] = None,
        include_metadata: bool = True,
        filter_fn: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Perform similarity search for multiple queries.
        
        Args:
            queries: List of query strings
            k: Number of results per query
            namespace: Optional namespace to search within
            include_metadata: Whether to include metadata in results
            filter_fn: Optional function to filter results
            
        Returns:
            List of results for each query
        """
        # Generate embeddings for all queries
        embeddings = self.generate_embeddings(queries)
        
        # Process each embedding
        results = []
        for embedding in embeddings:
            query_results = self.similarity_search_by_vector(
                embedding,
                k=k,
                namespace=namespace,
                include_metadata=include_metadata,
                filter_fn=filter_fn
            )
            results.append(query_results)
        
        return results
    
    def delete(self, ids: List[Union[str, int]]) -> None:
        """
        Delete vectors by ID.
        
        Note: FAISS requires rebuilding the index for deletion, which can be expensive.
        For simplicity, we just mark metadata as deleted for now.
        
        Args:
            ids: List of IDs to delete
        """
        if not self.index or self.index.ntotal == 0:
            return
        
        # Track if we need to save
        modified = False
        
        # Mark metadata as deleted
        for id_val in ids:
            # Find the metadata entry with this ID
            for idx, metadata_entry in enumerate(self.metadata):
                # Match either string ID or numeric index
                if (isinstance(id_val, str) and metadata_entry.get("id") == id_val) or \
                   (isinstance(id_val, int) and idx == id_val):
                    self.metadata[idx]["deleted"] = True
                    self.metadata[idx]["deleted_at"] = datetime.utcnow().isoformat()
                    
                    # Remove from namespace
                    namespace = metadata_entry.get("namespace")
                    if namespace and namespace in self.namespaces:
                        index_val = metadata_entry.get("index")
                        if index_val in self.namespaces[namespace]:
                            self.namespaces[namespace].remove(index_val)
                    
                    modified = True
        
        # Save if modified
        if modified:
            self._save_index()
            logger.info(f"Marked {len(ids)} vectors as deleted")
    
    def get_by_id(self, id_val: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata by ID.
        
        Args:
            id_val: ID to look up
            
        Returns:
            Metadata dictionary or None if not found
        """
        for metadata_entry in self.metadata:
            if metadata_entry.get("id") == id_val and not metadata_entry.get("deleted", False):
                return metadata_entry
        return None
    
    def get_by_namespace(self, namespace: str) -> List[Dict[str, Any]]:
        """
        Get all metadata entries in a namespace.
        
        Args:
            namespace: Namespace to look up
            
        Returns:
            List of metadata dictionaries
        """
        results = []
        for metadata_entry in self.metadata:
            if metadata_entry.get("namespace") == namespace and not metadata_entry.get("deleted", False):
                results.append(metadata_entry)
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary of statistics
        """
        # Count active vectors (not marked as deleted)
        active_vectors = sum(1 for m in self.metadata if not m.get("deleted", False))
        
        # Count vectors by namespace
        namespace_counts = {}
        for namespace, indices in self.namespaces.items():
            namespace_counts[namespace] = len(indices)
        
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "active_vectors": active_vectors,
            "deleted_vectors": len(self.metadata) - active_vectors,
            "namespaces": namespace_counts,
            "embedding_model": self.embedding_model_name,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "memory_usage_mb": self.index.ntotal * self.dimension * 4 / (1024 * 1024) if self.index else 0
        }
    
    def compute_relevance(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        """
        Compute relevance scores between a query and a list of texts.
        
        Args:
            query: Query text
            texts: List of texts to compute relevance for
            
        Returns:
            List of relevance scores [0-1]
        """
        # Generate embeddings
        query_embedding = self.generate_embedding(query)
        text_embeddings = self.generate_embeddings(texts)
        
        # Compute cosine similarities
        query_norm = np.linalg.norm(query_embedding)
        scores = []
        
        for text_embedding in text_embeddings:
            text_norm = np.linalg.norm(text_embedding)
            if query_norm == 0 or text_norm == 0:
                scores.append(0.0)
                continue
                
            dot_product = np.dot(query_embedding, text_embedding)
            similarity = dot_product / (query_norm * text_norm)
            
            # Convert to a score between 0 and 1
            score = (similarity + 1) / 2
            scores.append(float(score))
        
        return scores 