import logging
import random
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from config import settings

logger = logging.getLogger(__name__)

class APIManager:
    """
    Manages multiple API keys and providers (Google, Groq) to handle quota limits.
    Implements multi-provider rotation and failover.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(APIManager, cls).__new__(cls)
            cls._instance.google_keys = settings.GOOGLE_API_KEYS
            cls._instance.groq_key = settings.GROQ_API_KEY
            cls._instance.current_google_index = 0
            cls._instance.exhausted_keys: Dict[str, datetime] = {}
            cls._instance.quota_reset_minutes = 60
            cls._instance.active_provider = settings.EMBEDDING_PROVIDER.lower() if hasattr(settings, 'EMBEDDING_PROVIDER') else "google"
        return cls._instance
    
    def _is_key_available(self, key: str) -> bool:
        if not key or key not in self.exhausted_keys: return True
        reset_time = self.exhausted_keys[key] + timedelta(minutes=self.quota_reset_minutes)
        if datetime.now() >= reset_time:
            del self.exhausted_keys[key]
            return True
        return False

    def _mask_key(self, key: str) -> str:
        if not key or len(key) < 10: return "****"
        return f"{key[:7]}...{key[-4:]}"

    def get_active_provider(self) -> str:
        return self.active_provider

    def get_key(self) -> str:
        """Get key for current active provider."""
        if self.active_provider == "google":
            if not self.google_keys:
                if self.groq_key: 
                    self.active_provider = "groq"
                    return self.groq_key
                raise ValueError("No API keys configured")
            return self.google_keys[self.current_google_index]
        return self.groq_key or ""

    def rotate_key(self) -> Dict[str, str]:
        """
        Rotates to next Google key or fails over to Groq.
        Returns: {'provider': '...', 'model': '...', 'key': '...'}
        """
        if self.active_provider == "google":
            old_index = self.current_google_index
            self.exhausted_keys[self.google_keys[old_index]] = datetime.now()
            
            # Try next google key
            next_index = (old_index + 1) % len(self.google_keys)
            if self._is_key_available(self.google_keys[next_index]):
                self.current_google_index = next_index
                return {"provider": "google", "model": settings.LLM_MODEL, "key": self.google_keys[next_index]}
            
            # If all google keys exhausted, try Groq
            if self.groq_key and self._is_key_available(self.groq_key):
                logger.warning("🔥🔥 FAILOVER: All Google keys exhausted. Switching to GROQ provider.")
                self.active_provider = "groq"
                return {"provider": "groq", "model": settings.GROQ_MODEL, "key": self.groq_key}

        # If already on groq or failed over to groq
        if self.active_provider == "groq":
            logger.warning("Groq quota hit or already active. Resetting rotation.")
            self.active_provider = "google" # Reset to try google again
            self.current_google_index = 0
            return {"provider": "google", "model": settings.LLM_MODEL, "key": self.google_keys[0]}

        return {"provider": "google", "model": settings.LLM_MODEL, "key": self.google_keys[0]}

api_manager = APIManager()
