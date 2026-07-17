"""
Vector Store Module
===================
FAISS-based vector database for storing and retrieving document embeddings.
Supports efficient similarity search for RAG evidence retrieval.
"""

import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

try:
    import faiss
except ImportError:
    raise ImportError("Please install faiss-cpu: pip install faiss-cpu")

from .document_processor import DocumentChunk

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a search result from the vector store."""
    chunk: DocumentChunk
    score: float
    rank: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk.chunk_id,
            "content": self.chunk.content,
            "metadata": self.chunk.metadata,
            "score": self.score,
            "rank": self.rank,
        }


class EmbeddingService:
    """Handles text embedding generation using sentence transformers."""
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.device = device
        self._model = None
    
    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                raise ImportError("Please install sentence-transformers: pip install sentence-transformers")
        return self._model
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
            normalize_embeddings=True,  # For cosine similarity
        )
        
        return embeddings
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.embed_texts([text])[0]
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension()


class FAISSVectorStore:
    """FAISS-based vector store for document chunks."""
    
    def __init__(
        self,
        dimension: int = 384,
        index_type: str = "Flat",
        metric: str = "cosine",
    ):
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        
        # Initialize FAISS index
        self.index = self._create_index()
        
        # Metadata storage
        self.chunks: Dict[int, DocumentChunk] = {}
        self.chunk_id_to_index: Dict[str, int] = {}
        self._current_index = 0
    
    def _create_index(self) -> faiss.Index:
        """Create FAISS index based on configuration."""
        if self.metric == "cosine":
            # For cosine similarity, normalize vectors and use inner product
            if self.index_type == "Flat":
                index = faiss.IndexFlatIP(self.dimension)
            elif self.index_type == "IVFFlat":
                quantizer = faiss.IndexFlatIP(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, 100, faiss.METRIC_INNER_PRODUCT)
            else:
                index = faiss.IndexFlatIP(self.dimension)
        else:
            # L2 distance
            if self.index_type == "Flat":
                index = faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "IVFFlat":
                quantizer = faiss.IndexFlatL2(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            else:
                index = faiss.IndexFlatL2(self.dimension)
        
        return index
    
    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: np.ndarray,
    ) -> None:
        """Add document chunks with their embeddings to the index."""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        if len(chunks) == 0:
            return
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype(np.float32)
        
        # Normalize for cosine similarity
        if self.metric == "cosine":
            faiss.normalize_L2(embeddings)
        
        # Train index if needed (for IVF-based indices)
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            if len(embeddings) >= 100:
                self.index.train(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store chunk metadata
        for i, chunk in enumerate(chunks):
            idx = self._current_index + i
            self.chunks[idx] = chunk
            self.chunk_id_to_index[chunk.chunk_id] = idx
        
        self._current_index += len(chunks)
        logger.info(f"Added {len(chunks)} chunks to vector store. Total: {self._current_index}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        score_threshold: float = 0.0,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar chunks."""
        if self._current_index == 0:
            return []
        
        # Ensure query is 2D and float32
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        
        # Normalize for cosine similarity
        if self.metric == "cosine":
            faiss.normalize_L2(query_embedding)
        
        # Search more than needed if filtering
        search_k = min(top_k * 3 if filter_metadata else top_k, self._current_index)
        
        scores, indices = self.index.search(query_embedding, search_k)
        
        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            # Apply score threshold
            if score < score_threshold:
                continue
            
            chunk = self.chunks.get(idx)
            if chunk is None:
                continue
            
            # Apply metadata filter
            if filter_metadata:
                if not self._matches_filter(chunk.metadata, filter_metadata):
                    continue
            
            results.append(SearchResult(
                chunk=chunk,
                score=float(score),
                rank=len(results),
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_metadata: Dict[str, Any]) -> bool:
        """Check if chunk metadata matches filter criteria."""
        for key, value in filter_metadata.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False
        return True
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Retrieve a chunk by its ID."""
        idx = self.chunk_id_to_index.get(chunk_id)
        if idx is not None:
            return self.chunks.get(idx)
        return None
    
    def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete all chunks belonging to a document. Returns count deleted."""
        # Note: FAISS doesn't support direct deletion easily
        # We mark chunks as deleted and rebuild index periodically
        deleted_count = 0
        indices_to_remove = []
        
        for idx, chunk in self.chunks.items():
            if chunk.metadata.get("doc_id") == doc_id:
                indices_to_remove.append(idx)
                deleted_count += 1
        
        for idx in indices_to_remove:
            chunk_id = self.chunks[idx].chunk_id
            del self.chunks[idx]
            del self.chunk_id_to_index[chunk_id]
        
        logger.info(f"Marked {deleted_count} chunks for deletion from document {doc_id}")
        return deleted_count
    
    def save(self, path: Path) -> None:
        """Save the vector store to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))
        
        # Save metadata
        metadata = {
            "dimension": self.dimension,
            "index_type": self.index_type,
            "metric": self.metric,
            "current_index": self._current_index,
            "chunk_id_to_index": self.chunk_id_to_index,
        }
        with open(path / "metadata.json", "w") as f:
            json.dump(metadata, f)
        
        # Save chunks
        chunks_data = {
            idx: chunk.to_dict()
            for idx, chunk in self.chunks.items()
        }
        with open(path / "chunks.pkl", "wb") as f:
            pickle.dump(chunks_data, f)
        
        logger.info(f"Saved vector store to {path}")
    
    @classmethod
    def load(cls, path: Path) -> "FAISSVectorStore":
        """Load vector store from disk."""
        path = Path(path)
        
        # Load metadata
        with open(path / "metadata.json", "r") as f:
            metadata = json.load(f)
        
        # Create instance
        store = cls(
            dimension=metadata["dimension"],
            index_type=metadata["index_type"],
            metric=metadata["metric"],
        )
        
        # Load FAISS index
        store.index = faiss.read_index(str(path / "index.faiss"))
        store._current_index = metadata["current_index"]
        store.chunk_id_to_index = metadata["chunk_id_to_index"]
        
        # Load chunks
        with open(path / "chunks.pkl", "rb") as f:
            chunks_data = pickle.load(f)
        
        store.chunks = {
            int(idx): DocumentChunk.from_dict(data)
            for idx, data in chunks_data.items()
        }
        
        logger.info(f"Loaded vector store from {path} with {store._current_index} chunks")
        return store
    
    @property
    def count(self) -> int:
        """Get the number of chunks in the store."""
        return len(self.chunks)


class VectorStoreManager:
    """Manages multiple vector stores for different purposes."""
    
    def __init__(
        self,
        base_path: Path,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        self.stores: Dict[str, FAISSVectorStore] = {}
    
    def get_or_create_store(self, name: str) -> FAISSVectorStore:
        """Get existing store or create a new one."""
        if name in self.stores:
            return self.stores[name]
        
        store_path = self.base_path / name
        
        if store_path.exists() and (store_path / "index.faiss").exists():
            store = FAISSVectorStore.load(store_path)
        else:
            store = FAISSVectorStore(
                dimension=self.embedding_service.dimension,
                index_type="Flat",
                metric="cosine",
            )
        
        self.stores[name] = store
        return store
    
    def add_document_chunks(
        self,
        store_name: str,
        chunks: List[DocumentChunk],
    ) -> None:
        """Add document chunks to a store with automatic embedding."""
        store = self.get_or_create_store(store_name)
        
        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_texts(texts)
        
        # Add to store
        store.add_chunks(chunks, embeddings)
    
    def search(
        self,
        store_name: str,
        query: str,
        top_k: int = 5,
        **kwargs,
    ) -> List[SearchResult]:
        """Search a store with automatic query embedding."""
        store = self.get_or_create_store(store_name)
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        # Search
        return store.search(query_embedding, top_k=top_k, **kwargs)
    
    def save_all(self) -> None:
        """Save all stores to disk."""
        for name, store in self.stores.items():
            store.save(self.base_path / name)
