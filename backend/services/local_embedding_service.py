# Local Embedding Service
# ========================
# Powered by SentenceTransformers (HuggingFace)

import logging
from typing import List, Union
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)

class LocalEmbeddingService:
    """
    Local embedding service using HuggingFace models.
    Runs locally on CPU/GPU to bypass cloud API quota limits.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Initializing Local Embedding Service with model: {model_name} on {self.device}")
        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            logger.info("Local Embedding Service initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Local Embedding Service: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of documents."""
        try:
            embeddings = self.model.encode(texts, convert_to_list=True)
            return embeddings
        except Exception as e:
            logger.error(f"Local document embedding failed: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        try:
            embedding = self.model.encode(text, convert_to_list=True)
            return embedding
        except Exception as e:
            logger.error(f"Local query embedding failed: {e}")
            raise

    @property
    def dimension(self) -> int:
        """Return the dimension of the embeddings (384 for all-MiniLM-L6-v2)."""
        return self.model.get_sentence_embedding_dimension()
