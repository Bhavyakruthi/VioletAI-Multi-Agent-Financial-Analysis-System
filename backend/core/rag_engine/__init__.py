"""
RAG Engine Module
=================
Provides document-based Retrieval-Augmented Generation capabilities
for the equity research pipeline.
"""

from .document_processor import DocumentProcessor
from .rag_tools import create_rag_tools
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Unified interface for the document RAG system.
    
    This class provides a simple API to:
    1. Load and index financial documents (PDF, TXT, DOCX)
    2. Search for relevant context using semantic similarity
    3. Provide CrewAI tools for agent-based document analysis
    
    Example:
        >>> rag = RAGEngine()
        >>> rag.load_documents(["./annual_report.pdf"])
        >>> results = rag.search("What was the revenue growth?")
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the RAG Engine.
        
        Args:
            chunk_size: Size of text chunks for document splitting
            chunk_overlap: Overlap between consecutive chunks
        """
        self.processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self._tools = None
        self._is_initialized = False
        logger.info("RAG Engine initialized")
    
    def load_documents(self, file_paths: List[str]) -> int:
        """
        Load and index a list of document file paths.
        
        Args:
            file_paths: List of paths to PDF, TXT, or DOCX files
            
        Returns:
            Number of document chunks indexed
        """
        total_chunks = 0
        for path in file_paths:
            try:
                docs = self.processor.load_document(path)
                self.processor.create_vector_store(docs)
                total_chunks += len(docs)
                logger.info(f"Loaded: {path}")
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
                continue
        
        self._is_initialized = True
        print(f"✅ Indexed {len(file_paths)} documents ({total_chunks} chunks)")
        return total_chunks
    
    def load_uploaded_files(self, uploaded_files: List) -> int:
        """
        Load documents from Streamlit UploadedFile objects.
        
        Args:
            uploaded_files: List of Streamlit UploadedFile objects
            
        Returns:
            Number of document chunks indexed
        """
        return self.processor.add_documents(uploaded_files)
    
    def search(self, query: str, k: int = 5) -> List:
        """
        Search indexed documents for relevant context.
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of relevant Document objects with page_content and metadata
        """
        if not self._is_initialized:
            logger.warning("No documents loaded. Call load_documents() first.")
            return []
        
        return self.processor.similarity_search(query, k=k)
    
    def get_context_for_query(self, query: str, k: int = 5) -> str:
        """
        Get formatted context string for a query.
        
        Args:
            query: Search query
            k: Number of chunks to retrieve
            
        Returns:
            Formatted string with relevant document excerpts
        """
        results = self.search(query, k=k)
        if not results:
            return ""
        
        context_parts = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "N/A")
            context_parts.append(
                f"[Source: {source}, Page: {page}]\n{doc.page_content}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    def get_all_text(self) -> str:
        """Get all loaded document text concatenated."""
        return self.processor.get_all_text()
    
    def get_document_list(self) -> List[str]:
        """Get list of loaded document names."""
        return self.processor.get_document_list()
    
    @property
    def tools(self):
        """
        Lazily create and return CrewAI tools for document operations.
        
        Returns:
            List of CrewAI BaseTool instances
        """
        if self._tools is None:
            self._tools = create_rag_tools(self.processor)
        return self._tools
    
    @property
    def is_ready(self) -> bool:
        """Check if documents have been loaded."""
        return self._is_initialized and self.processor.vector_store is not None
    
    def clear(self):
        """Clear all loaded documents and reset the engine."""
        self.processor.clear()
        self._tools = None
        self._is_initialized = False
        logger.info("RAG Engine cleared")


__all__ = ["RAGEngine", "DocumentProcessor", "create_rag_tools"]
