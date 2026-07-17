# Documents Routes
# ================
# Document upload and management with per-user ChromaDB

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime
import os
import shutil
import logging

from api.dependencies import get_current_user
from services.chroma_service import ChromaService
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    size_bytes: int
    chunk_count: int
    uploaded_at: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    total_count: int


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    message: str


class SearchResult(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    score: float


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


# ============================================================================
# Routes
# ============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(default="general"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a document and index it in the user's ChromaDB collection.
    
    Supported formats: PDF, DOCX, TXT
    """
    user_id = current_user["id"]
    
    # Validate file type
    allowed_extensions = [".pdf", ".docx", ".txt"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed_extensions}"
        )
    
    try:
        # Create temp directory for user uploads
        upload_dir = f"./uploads/{user_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file temporarily
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Initialize services
        embedding_service = EmbeddingService()
        chroma_service = ChromaService(user_id)
        
        # Process document and create embeddings
        document_id = str(uuid4())
        chunks_created = await chroma_service.ingest_document(
            file_path=file_path,
            document_id=document_id,
            filename=file.filename,
            doc_type=doc_type,
            embedding_service=embedding_service
        )
        
        # Clean up temp file (keep it if you want to store originals)
        # os.remove(file_path)
        
        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            chunks_created=chunks_created,
            message="Document uploaded and indexed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: dict = Depends(get_current_user)
):
    """
    List all documents for the current user.
    """
    user_id = current_user["id"]
    
    try:
        chroma_service = ChromaService(user_id)
        documents = chroma_service.list_documents()
        
        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a document and its vectors from ChromaDB.
    """
    user_id = current_user["id"]
    
    try:
        chroma_service = ChromaService(user_id)
        deleted = chroma_service.delete_document(document_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=List[SearchResult])
async def search_documents(
    request: SearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Semantic search across user's documents.
    """
    user_id = current_user["id"]
    
    try:
        embedding_service = EmbeddingService()
        chroma_service = ChromaService(user_id)
        
        results = await chroma_service.search(
            query=request.query,
            top_k=request.top_k,
            embedding_service=embedding_service
        )
        
        return [
            SearchResult(
                content=r["content"],
                source=r["source"],
                page=r.get("page"),
                score=r["score"]
            )
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
