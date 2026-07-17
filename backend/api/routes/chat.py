# Chat Routes
# ============
# RAG Chatbot with WebSocket streaming

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging

from api.dependencies import get_current_user, get_supabase_client
from services.chat_service import ChatService
from services.chroma_service import ChromaService
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context_mode: str = "documents"  # "documents", "stock", "both"
    ticker: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    timestamp: str


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]
    total_count: int


# In-memory chat history (replace with Redis/DB in production)
chat_histories: Dict[str, List[ChatMessage]] = {}


# ============================================================================
# REST Endpoints
# ============================================================================

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message and get a response with RAG context.
    """
    user_id = current_user["id"]
    
    try:
        embedding_service = EmbeddingService()
        chroma_service = ChromaService(user_id)
        chat_service = ChatService()
        
        # Search for relevant context
        context_results = await chroma_service.search(
            query=request.message,
            top_k=5,
            embedding_service=embedding_service
        )
        
        # Build context string
        context = "\n\n".join([
            f"[Source: {r['source']}]\n{r['content']}"
            for r in context_results
        ])
        
        # Generate response
        response = await chat_service.generate_response(
            message=request.message,
            context=context,
            ticker=request.ticker
        )
        
        # Format sources
        sources = [
            {
                "source": r["source"],
                "page": r.get("page"),
                "snippet": r["content"][:200] + "..."
            }
            for r in context_results
        ]
        
        timestamp = datetime.now().isoformat()
        
        # Save to history
        if user_id not in chat_histories:
            chat_histories[user_id] = []
        
        chat_histories[user_id].append(ChatMessage(
            role="user",
            content=request.message,
            timestamp=timestamp
        ))
        chat_histories[user_id].append(ChatMessage(
            role="assistant",
            content=response,
            sources=sources,
            timestamp=timestamp
        ))
        
        return ChatResponse(
            response=response,
            sources=sources,
            timestamp=timestamp
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Get chat history for the current user.
    """
    user_id = current_user["id"]
    
    messages = chat_histories.get(user_id, [])[-limit:]
    
    return ChatHistoryResponse(
        messages=messages,
        total_count=len(messages)
    )


@router.delete("/history")
async def clear_chat_history(
    current_user: dict = Depends(get_current_user)
):
    """
    Clear chat history for the current user.
    """
    user_id = current_user["id"]
    
    if user_id in chat_histories:
        chat_histories[user_id] = []
    
    return {"message": "Chat history cleared"}


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming chat.
    """
    await websocket.accept()
    
    user_id = None
    
    try:
        # First message should be auth token
        auth_data = await websocket.receive_text()
        auth_json = json.loads(auth_data)
        token = auth_json.get("token")
        
        if not token:
            await websocket.send_json({"error": "Authentication required"})
            await websocket.close(code=4001)
            return
        
        # Verify token
        try:
            supabase = get_supabase_client()
            user_response = supabase.auth.get_user(token)
            if not user_response or not user_response.user:
                await websocket.send_json({"error": "Invalid token"})
                await websocket.close(code=4001)
                return
            user_id = user_response.user.id
        except Exception as e:
            await websocket.send_json({"error": "Authentication failed"})
            await websocket.close(code=4001)
            return
        
        await websocket.send_json({"status": "connected", "user_id": user_id})
        
        embedding_service = EmbeddingService()
        chroma_service = ChromaService(user_id)
        chat_service = ChatService()
        
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            ticker = message_data.get("ticker")
            document_ids = message_data.get("document_ids", [])  # Expecting a list from frontend
            
            # Send typing indicator
            await websocket.send_json({"type": "typing", "status": True})
            
            # Search for context across ALL selected documents
            context_results = await chroma_service.search(
                query=user_message,
                top_k=5,
                embedding_service=embedding_service,
                document_ids=document_ids
            )
            
            # Build context
            context = "\n\n".join([
                f"[Source: {r['source']}]\n{r['content']}"
                for r in context_results
            ])
            
            # Stream response
            async for chunk in chat_service.generate_response_stream(
                message=user_message,
                context=context,
                ticker=ticker
            ):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk
                })
            
            # Send sources
            sources = [
                {
                    "source": r["source"],
                    "page": r.get("page"),
                    "snippet": r["content"][:200]
                }
                for r in context_results
            ]
            
            await websocket.send_json({
                "type": "sources",
                "sources": sources
            })
            
            # Send done indicator
            await websocket.send_json({
                "type": "done",
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})
