"""
Document Processor for RAG System
=================================
Handles document loading, chunking, and vector store creation.
"""

import os
import tempfile
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
from dotenv import load_dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredFileLoader,
)
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.schema import Document

load_dotenv()

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document processing, chunking, and vector store management."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_model: str = None,
    ):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
            embedding_model: HuggingFace embedding model to use
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        
        # Use HuggingFace embeddings (free)
        embedding_model = embedding_model or os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        
        self.vector_store: Optional[FAISS] = None
        self.documents: List[Document] = []
        self.document_metadata: Dict[str, Any] = {}
    
    def load_document(self, file_path: str) -> List[Document]:
        """
        Load a document based on its file extension.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of Document objects
        """
        file_extension = Path(file_path).suffix.lower()
        
        try:
            if file_extension == ".pdf":
                loader = PyPDFLoader(file_path)
            elif file_extension == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
            elif file_extension in [".docx", ".doc"]:
                loader = Docx2txtLoader(file_path)
            else:
                loader = UnstructuredFileLoader(file_path)
            
            documents = loader.load()
            
            # Add source metadata
            for doc in documents:
                doc.metadata["source"] = Path(file_path).name
                doc.metadata["file_path"] = file_path
            
            logger.info(f"Loaded {len(documents)} pages from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            raise
    
    def load_from_uploaded_file(self, uploaded_file) -> List[Document]:
        """
        Load a document from a Streamlit uploaded file.
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            List of Document objects
        """
        # Save to temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=Path(uploaded_file.name).suffix
        ) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            documents = self.load_document(tmp_path)
            # Update source to original filename
            for doc in documents:
                doc.metadata["source"] = uploaded_file.name
            return documents
        finally:
            # Clean up temp file
            os.unlink(tmp_path)
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of chunked Document objects
        """
        chunks = self.text_splitter.split_documents(documents)
        
        # Add chunk metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = i
        
        logger.info(f"Split into {len(chunks)} chunks")
        return chunks
    
    # def create_vector_store(self, documents: List[Document]) -> FAISS:
    #     """
    #     Create a FAISS vector store from documents.
        
    #     Args:
    #         documents: List of Document objects
            
    #     Returns:
    #         FAISS vector store
    #     """
    #     chunks = self.process_documents(documents)
    #     self.documents.extend(chunks)
        
    #     if self.vector_store is None:
    #         self.vector_store = FAISS.from_documents(chunks, self.embeddings)
    #     else:
    #         # Add to existing vector store
    #         new_store = FAISS.from_documents(chunks, self.embeddings)
    #         self.vector_store.merge_from(new_store)
        
    #     logger.info(f"Vector store created/updated with {len(chunks)} chunks")
    #     return self.vector_store
    
    def add_documents(self, uploaded_files: List) -> int:
        """
        Add multiple uploaded files to the vector store.
        
        Args:
            uploaded_files: List of Streamlit UploadedFile objects
            
        Returns:
            Number of documents processed
        """
        all_documents = []
        
        for uploaded_file in uploaded_files:
            try:
                docs = self.load_from_uploaded_file(uploaded_file)
                all_documents.extend(docs)
                self.document_metadata[uploaded_file.name] = {
                    "pages": len(docs),
                    "size": uploaded_file.size,
                }
            except Exception as e:
                logger.error(f"Error processing {uploaded_file.name}: {e}")
                continue
        
        if all_documents:
            self.create_vector_store(all_documents)
        
        return len(all_documents)
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Document]:
        """
        Perform similarity search on the vector store.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of relevant Document objects
        """
        if self.vector_store is None:
            logger.warning("No vector store available")
            return []
        
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        # Filter by score threshold and return documents
        filtered_results = [
            doc for doc, score in results if score >= score_threshold
        ]
        
        return filtered_results
    
    def get_all_text(self) -> str:
        """
        Get all document text concatenated.
        
        Returns:
            String containing all document text
        """
        return "\n\n".join([doc.page_content for doc in self.documents])
    
    def get_document_list(self) -> List[str]:
        """
        Get list of loaded document names.
        
        Returns:
            List of document names
        """
        return list(self.document_metadata.keys())
    
    def clear(self):
        """Clear all loaded documents and vector store."""
        self.vector_store = None
        self.documents = []
        self.document_metadata = {}
        logger.info("Document processor cleared")
