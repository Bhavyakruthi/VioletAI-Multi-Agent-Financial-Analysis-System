# ChromaDB Service
# =================
# Per-user document storage using ChromaDB

import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from uuid import uuid4
import logging
import json

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class ChromaService:
    """
    Per-user ChromaDB service for document storage and retrieval.
    
    Each user gets their own isolated ChromaDB collection, ensuring
    complete data separation between users.
    """
    
    def __init__(self, user_id: str):
        """
        Initialize ChromaDB for a specific user.
        
        Args:
            user_id: Unique user identifier (from Supabase)
        """
        self.user_id = user_id
        self.collection_name = f"user_{user_id}"
        
        # Create user-specific persist directory
        base_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.persist_dir = os.path.join(base_dir, user_id)
        os.makedirs(self.persist_dir, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"user_id": user_id}
        )
        
        # Document metadata storage
        self.metadata_file = os.path.join(self.persist_dir, "documents.json")
        self.document_metadata = self._load_metadata()
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load document metadata from file."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Save document metadata to file."""
        with open(self.metadata_file, "w") as f:
            json.dump(self.document_metadata, f, indent=2)
    
    async def ingest_document(
        self,
        file_path: str,
        document_id: str,
        filename: str,
        doc_type: str,
        embedding_service
    ) -> int:
        """
        Ingest a document into ChromaDB.
        
        Args:
            file_path: Path to the document file
            document_id: Unique document identifier
            filename: Original filename
            doc_type: Type of document (e.g., "annual_report")
            embedding_service: CohereEmbeddingService instance
            
        Returns:
            Number of chunks created
        """
        # Load document based on file type
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif file_ext == ".txt":
            loader = TextLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Load and split document
        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)
        
        if not chunks:
            raise ValueError("No content extracted from document")
        
        # Prepare data for ChromaDB
        texts = [chunk.page_content for chunk in chunks]
        
        # Generate embeddings
        embeddings = await embedding_service.embed_documents_async(texts)
        
        # Prepare IDs and metadata
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "doc_type": doc_type,
                "chunk_index": i,
                "page": chunk.metadata.get("page", 0),
                "source": filename
            }
            for i, chunk in enumerate(chunks)
        ]
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        # Save document metadata
        self.document_metadata[document_id] = {
            "id": document_id,
            "filename": filename,
            "file_type": file_ext,
            "doc_type": doc_type,
            "chunk_count": len(chunks),
            "uploaded_at": datetime.now().isoformat(),
            "size_bytes": os.path.getsize(file_path)
        }
        self._save_metadata()
        
        logger.info(f"Ingested document {filename} with {len(chunks)} chunks")
        return len(chunks)
    
    async def ingest_report_text(
        self,
        report_text: str,
        document_id: str,
        filename: str,
        ticker: str,
        report_type: str,
        embedding_service,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Ingest a generated report directly from text into ChromaDB.
        
        Args:
            report_text: The report text content
            document_id: Unique document identifier
            filename: Display name for the report
            ticker: Stock ticker associated with report
            report_type: Type of report (e.g., "research_report", "analysis")
            embedding_service: CohereEmbeddingService instance
            extra_metadata: Optional additional metadata
            
        Returns:
            Number of chunks created
        """
        if not report_text or len(report_text.strip()) < 50:
            logger.warning("Report text too short to ingest")
            return 0
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(report_text)
        
        if not chunks:
            logger.warning("No chunks generated from report text")
            return 0
        
        # Generate embeddings
        embeddings = await embedding_service.embed_documents_async(chunks)
        
        # Prepare IDs and metadata
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        base_metadata = {
            "document_id": document_id,
            "filename": filename,
            "doc_type": report_type,
            "ticker": ticker,
            "source": "generated_report",
            "generated_at": datetime.now().isoformat()
        }
        
        if extra_metadata:
            base_metadata.update(extra_metadata)
        
        metadatas = [
            {**base_metadata, "chunk_index": i}
            for i in range(len(chunks))
        ]
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        # Save document metadata
        self.document_metadata[document_id] = {
            "id": document_id,
            "filename": filename,
            "file_type": "generated_report",
            "doc_type": report_type,
            "ticker": ticker,
            "chunk_count": len(chunks),
            "uploaded_at": datetime.now().isoformat(),
            "size_bytes": len(report_text.encode('utf-8'))
        }
        self._save_metadata()
        
        logger.info(f"Ingested generated report '{filename}' for {ticker} with {len(chunks)} chunks")
        return len(chunks)
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents for this user.
        
        Returns:
            List of document metadata
        """
        return [
            {
                "id": doc_id,
                "filename": meta["filename"],
                "file_type": meta["file_type"],
                "size_bytes": meta.get("size_bytes", 0),
                "chunk_count": meta["chunk_count"],
                "uploaded_at": meta["uploaded_at"]
            }
            for doc_id, meta in self.document_metadata.items()
        ]
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its vectors.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if document_id not in self.document_metadata:
            return False
        
        # Get all chunk IDs for this document
        chunk_count = self.document_metadata[document_id]["chunk_count"]
        ids_to_delete = [f"{document_id}_{i}" for i in range(chunk_count)]
        
        # Delete from ChromaDB
        self.collection.delete(ids=ids_to_delete)
        
        # Remove from metadata
        del self.document_metadata[document_id]
        self._save_metadata()
        
        logger.info(f"Deleted document {document_id}")
        return True
    
    def reset_knowledge_base(self):
        """
        Completely reset the user's knowledge base.
        Deletes the collection and the metadata file.
        Use this when switching embedding providers to avoid dimension mismatches.
        """
        try:
            # Delete collection from Chroma
            self.client.delete_collection(self.collection_name)
            
            # Re-create empty collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"user_id": self.user_id}
            )
            
            # Reset metadata
            self.document_metadata = {}
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            self._save_metadata()
            
            logger.info(f"Successfully reset knowledge base for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reset knowledge base: {e}")
            return False
    
    async def search(
        self,
        query: str,
        top_k: int,
        embedding_service,
        document_ids: Optional[Union[str, List[str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks across one or more documents.
        """
        # Generate query embedding
        query_embedding = await embedding_service.embed_query_async(query)
        
        # Build where clause for filtering
        where = None
        if document_ids:
            if isinstance(document_ids, str):
                where = {"document_id": document_ids}
            elif isinstance(document_ids, list) and len(document_ids) > 0:
                if len(document_ids) == 1:
                    where = {"document_id": document_ids[0]}
                else:
                    where = {"document_id": {"$in": document_ids}}
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if results["distances"] else 0
                
                # Convert distance to similarity score (0-1)
                score = 1 - (distance / 2) if distance < 2 else 0
                
                search_results.append({
                    "content": doc,
                    "source": metadata.get("filename", "Unknown"),
                    "page": metadata.get("page"),
                    "document_id": metadata.get("document_id"),
                    "score": round(score, 4)
                })
        
        return search_results
    
    def get_document_chunks(self, document_ids: Union[str, List[str]]) -> List[str]:
        """
        Get all chunks for one or more specific documents.
        """
        if isinstance(document_ids, str):
            document_ids = [document_ids]
            
        all_ids = []
        for doc_id in document_ids:
            if doc_id in self.document_metadata:
                chunk_count = self.document_metadata[doc_id]["chunk_count"]
                all_ids.extend([f"{doc_id}_{i}" for i in range(chunk_count)])
        
        if not all_ids:
            return []
            
        # Chroma collection.get can handle large lists of IDs
        results = self.collection.get(
            ids=all_ids,
            include=["documents"]
        )
        
        return results["documents"] if results["documents"] else []
