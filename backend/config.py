# Backend Configuration
# =====================

import torch
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )
    
    # App
    APP_NAME: str = "AI Equity Research API"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"
    EMBEDDING_PROVIDER: str = "google"  # Options: google, local, cohere
    USE_LOCAL_EMBEDDINGS: bool = False  # Legacy toggle, preferred using EMBEDDING_PROVIDER
    
    # Supabase
    SKIP_SUPABASE: bool = False
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    # Cohere
    COHERE_API_KEY: str = ""
    COHERE_EMBED_MODEL: str = "embed-english-v3.0"
    
    # Google Gemini
    GOOGLE_API_KEY: str = ""
    GOOGLE_API_KEY_2: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_TEMPERATURE: float = 0.1
    
    # Groq Fallback
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "groq/llama-3.3-70b-versatile" # Premium fallback model
    
    @property
    def GOOGLE_API_KEYS(self) -> List[str]:
        keys = [self.GOOGLE_API_KEY]
        if self.GOOGLE_API_KEY_2:
            keys.append(self.GOOGLE_API_KEY_2)
        return [k for k in keys if k]
    
    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]
    
    # Email (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@aiequityresearch.com"

    # Device
    @property
    def DEVICE(self) -> str:
        return "cuda" if torch.cuda.is_available() else "cpu"


settings = Settings()
