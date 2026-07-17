# Google Embedding Service
# =========================
# Uses Google's generative-ai SDK for document embeddings

import os
import google.generativeai as genai
from typing import List, Optional
import logging
from dotenv import load_dotenv

from core.api_manager import api_manager

load_dotenv()
logger = logging.getLogger(__name__)


import cohere
from .local_embedding_service import LocalEmbeddingService
from config import settings

class GoogleEmbeddingService:
    # ... (existing code remains or matches common signature)
    def __init__(self):
        self.api_manager = api_manager
        self.model = "models/text-embedding-004"
        genai.configure(api_key=self.api_manager.get_key())
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts: return []
        batch_size = 100
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                result = genai.embed_content(model=self.model, content=batch, task_type="retrieval_document")
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    logger.warning("Quota exceeded for document embedding. Rotating key.")
                    genai.configure(api_key=self.api_manager.rotate_key())
                    result = genai.embed_content(model=self.model, content=batch, task_type="retrieval_document")
                else: raise
            all_embeddings.extend(result['embedding'])
        return all_embeddings
    
    def embed_query(self, query: str) -> List[float]:
        if not query: return []
        try:
            try:
                result = genai.embed_content(model=self.model, content=query, task_type="retrieval_query")
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    logger.warning("Quota exceeded for query embedding. Rotating key.")
                    genai.configure(api_key=self.api_manager.rotate_key())
                    result = genai.embed_content(model=self.model, content=query, task_type="retrieval_query")
                else: raise
            return result['embedding']
        except Exception as e: raise

class CohereEmbeddingService:
    """
    Embedding service using Cohere API.
    """
    def __init__(self):
        self.client = cohere.Client(settings.COHERE_API_KEY)
        self.model = settings.COHERE_EMBED_MODEL
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts: return []
        response = self.client.embed(
            texts=texts,
            model=self.model,
            input_type="search_document",
            embedding_types=["float"]
        )
        return response.embeddings.float
    
    def embed_query(self, query: str) -> List[float]:
        if not query: return []
        response = self.client.embed(
            texts=[query],
            model=self.model,
            input_type="search_query",
            embedding_types=["float"]
        )
        return response.embeddings.float[0]

class EmbeddingService:
    """
    Factory service that routes embedding requests.
    Now supports Google, Local, and Cohere providers.
    """
    def __init__(self):
        provider = settings.EMBEDDING_PROVIDER.lower()
        
        # Backward compatibility for legacy toggle
        if settings.USE_LOCAL_EMBEDDINGS:
            provider = "local"
            
        if provider == "local":
            logger.info("Initializing system with LOCAL Embeddings (CPU/GPU).")
            self.provider = LocalEmbeddingService()
        elif provider == "cohere":
            logger.info("Initializing system with COHERE Embeddings.")
            self.provider = CohereEmbeddingService()
        else:
            logger.info("Initializing system with GOOGLE Cloud Embeddings.")
            self.provider = GoogleEmbeddingService()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.provider.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        return self.provider.embed_query(query)

    async def embed_documents_async(self, texts: List[str]) -> List[List[float]]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_documents, texts)
    
    async def embed_query_async(self, query: str) -> List[float]:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_query, query)
