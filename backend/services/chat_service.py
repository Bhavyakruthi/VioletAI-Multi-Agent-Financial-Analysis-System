# Chat Service
# =============
# RAG-powered chat with Google Gemini

import os
import google.generativeai as genai
from typing import Optional, AsyncIterator
import logging
from dotenv import load_dotenv

from config import settings
from core.api_manager import api_manager

load_dotenv()
logger = logging.getLogger(__name__)


class ChatService:
    """
    Chat service using Google Gemini for response generation.
    
    Integrates retrieved document context for RAG-powered responses.
    """
    
    def __init__(self):
        self.api_manager = api_manager
        
        # Initial configuration
        genai.configure(api_key=self.api_manager.get_key())
        self.model = genai.GenerativeModel(settings.LLM_MODEL)
        
        # System prompt for financial analysis context
        self.system_prompt = """You are an AI financial research assistant specializing in equity analysis.
Your role is to provide accurate, evidence-based answers using the context provided from uploaded financial documents.

Guidelines:
1. Base your answers primarily on the provided document context
2. If the context doesn't contain relevant information, say so clearly
3. Always cite your sources when referencing specific data
4. Provide balanced, professional analysis
5. Avoid speculation - stick to facts from the documents
6. Format responses clearly with bullet points and headers when appropriate"""

    async def generate_response(self, message: str, context: str, ticker: Optional[str] = None) -> str:
        prompt_parts = [self.system_prompt]
        if context: prompt_parts.append(f"\n\n## Relevant Document Context:\n{context}")
        if ticker: prompt_parts.append(f"\n\n## Stock Being Analyzed: {ticker}")
        prompt_parts.append(f"\n\n## User Question:\n{message}\n\n## Your Response:")
        full_prompt = "\n".join(prompt_parts)
        
        max_retries = 3
        last_error = ""
        
        for attempt in range(max_retries):
            try:
                # Use active provider
                active_provider = self.api_manager.get_active_provider()
                if active_provider == "google":
                    response = self.model.generate_content(full_prompt)
                    return response.text
                else:
                    # Generic LiteLLM fallback for Groq
                    import litellm
                    resp = litellm.completion(
                        model=settings.GROQ_MODEL,
                        messages=[{"role": "user", "content": full_prompt}],
                        api_key=self.api_manager.get_key()
                    )
                    return resp.choices[0].message.content
            except Exception as e:
                last_error = str(e)
                if "429" in last_error or "quota" in last_error.lower():
                    logger.warning(f"Quota exceeded (attempt {attempt+1}/{max_retries}). Rotating provider.")
                    rotation_data = self.api_manager.rotate_key()
                    
                    # Update local model instance if provider is still google (or changed to google)
                    if rotation_data.get("provider") == "google":
                        genai.configure(api_key=rotation_data.get("key"))
                        self.model = genai.GenerativeModel(settings.LLM_MODEL)
                    
                    # Continue to next attempt
                    continue
                else:
                    # Non-quota error, don't retry
                    logger.error(f"Non-quota error in attempt {attempt+1}: {e}")
                    break
        
        error_msg = f"I apologize, but I encountered an error after multiple attempts: {last_error}"
        logger.error(error_msg)
        return error_msg
    
    async def generate_response_stream(self, message: str, context: str, ticker: Optional[str] = None) -> AsyncIterator[str]:
        # Simple non-streaming fallback for now to ensure robustness during key rotation
        response = await self.generate_response(message, context, ticker)
        yield response
