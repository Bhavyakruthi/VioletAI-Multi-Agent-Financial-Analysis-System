"""
Configuration settings for the RAG Evidence Agent system.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EmbeddingConfig:
    """Configuration for embedding models."""
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    batch_size: int = 32
    max_seq_length: int = 512


@dataclass
class VectorStoreConfig:
    """Configuration for FAISS vector store."""
    index_type: str = "IVFFlat"  # Options: Flat, IVFFlat, IVFPQ
    nlist: int = 100  # Number of clusters for IVF
    nprobe: int = 10  # Number of clusters to search
    metric: str = "cosine"  # Options: cosine, l2, ip


@dataclass
class ChunkingConfig:
    """Configuration for document chunking."""
    chunk_size: int = 500
    chunk_overlap: int = 50
    min_chunk_size: int = 100
    separators: list = field(default_factory=lambda: ["\n\n", "\n", ". ", " "])


@dataclass
class RetrievalConfig:
    """Configuration for retrieval settings."""
    top_k: int = 5
    score_threshold: float = 0.5
    rerank: bool = True
    max_context_length: int = 4000


@dataclass
class LLMConfig:
    """Configuration for LLM settings."""
    provider: str = "gemini"  # Options: gemini, openai
    model: str = "gemini-2.5-flash"  # Free tier model - best rate limits
    temperature: float = 0.1
    max_tokens: int = 2000
    api_key: Optional[str] = None
    
    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


@dataclass
class RAGConfig:
    """Main configuration class for RAG system."""
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # Paths
    data_dir: Path = field(default_factory=lambda: Path("data"))
    index_dir: Path = field(default_factory=lambda: Path("data/indices"))
    cache_dir: Path = field(default_factory=lambda: Path("data/cache"))
    
    def __post_init__(self):
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


# Default configuration instance
default_config = RAGConfig()


def get_config() -> RAGConfig:
    """Get the default RAG configuration."""
    return default_config


def load_config_from_env() -> RAGConfig:
    """Load configuration from environment variables."""
    return RAGConfig(
        embedding=EmbeddingConfig(
            model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            dimension=int(os.getenv("EMBEDDING_DIMENSION", 384)),
        ),
        retrieval=RetrievalConfig(
            top_k=int(os.getenv("RETRIEVAL_TOP_K", 5)),
            score_threshold=float(os.getenv("RETRIEVAL_THRESHOLD", 0.5)),
        ),
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "gemini"),
            model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
            temperature=float(os.getenv("LLM_TEMPERATURE", 0.1)),
            api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
        ),
        data_dir=Path(os.getenv("DATA_DIR", "data")),
        index_dir=Path(os.getenv("INDEX_DIR", "data/indices")),
        cache_dir=Path(os.getenv("CACHE_DIR", "data/cache")),
    )
