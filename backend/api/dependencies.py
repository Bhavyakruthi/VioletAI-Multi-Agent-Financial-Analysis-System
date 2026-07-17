# API Dependencies
# =================
# Shared dependencies for authentication and common utilities

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from typing import Optional
import logging
import json
import os

from config import settings

logger = logging.getLogger(__name__)

# Security scheme (lenient for testing/bypass)
security = HTTPBearer(auto_error=False)


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Verify JWT token and return current user.
    
    This dependency validates the Supabase JWT token and returns
    the authenticated user's information.
    """
    # Bypass Supabase if configured
    if settings.SKIP_SUPABASE:
        # Try to load last registered user from local file
        if os.path.exists("users.json"):
            try:
                with open("users.json", "r") as f:
                    users = json.load(f)
                    if users:
                        last_user = users[-1]
                        return {
                            "id": last_user["id"],
                            "email": last_user["email"],
                            "user_metadata": last_user.get("user_metadata", {}),
                            "created_at": last_user.get("created_at")
                        }
            except Exception as e:
                logger.warning(f"Failed to load local users: {e}")

        # Fallback to demo user if no local file
        return {
            "id": "00000000-0000-0000-0000-000000000000",
            "email": "demo@example.com",
            "user_metadata": {"full_name": "Demo User"},
            "created_at": "2024-01-01T00:00:00Z"
        }
        
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    token = credentials.credentials
    
    try:
        supabase = get_supabase_client()
        
        # Verify the JWT token with Supabase
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = user_response.user
        
        return {
            "id": user.id,
            "email": user.email,
            "user_metadata": user.user_metadata,
            "created_at": str(user.created_at) if user.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[dict]:
    """
    Optionally get current user (for endpoints that work with or without auth).
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
