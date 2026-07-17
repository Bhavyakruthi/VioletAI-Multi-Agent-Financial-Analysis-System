# Auth Routes
# ============
# Supabase JWT verification endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from api.dependencies import get_current_user, get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class UserResponse(BaseModel):
    id: str
    email: str
    user_metadata: Optional[dict] = None
    created_at: Optional[str] = None


class TokenVerifyRequest(BaseModel):
    token: str


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None


# ============================================================================
# Routes
# ============================================================================

@router.post("/verify", response_model=AuthStatusResponse)
async def verify_token(request: TokenVerifyRequest):
    """
    Verify a Supabase JWT token.
    
    This endpoint is used by the frontend to validate tokens
    without requiring the full auth header setup.
    """
    try:
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(request.token)
        
        if not user_response or not user_response.user:
            return AuthStatusResponse(authenticated=False, user=None)
        
        user = user_response.user
        return AuthStatusResponse(
            authenticated=True,
            user=UserResponse(
                id=user.id,
                email=user.email,
                user_metadata=user.user_metadata,
                created_at=str(user.created_at) if user.created_at else None
            )
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return AuthStatusResponse(authenticated=False, user=None)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        user_metadata=current_user.get("user_metadata"),
        created_at=current_user.get("created_at")
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout endpoint (mainly for audit/logging purposes).
    
    Note: Actual session invalidation is handled by Supabase on the client.
    """
    logger.info(f"User {current_user['email']} logged out")
    return {"message": "Logged out successfully", "user_id": current_user["id"]}


# ============================================================================
# Local Auth (When SKIP_SUPABASE is True)
# ============================================================================

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = "Trader"

import json
import os
from uuid import uuid4
from config import settings

USERS_FILE = "users.json"

@router.post("/signup", status_code=201)
async def local_signup(request: SignupRequest):
    """
    Local signup endpoint for development/testing (bypasses Supabase).
    Stores user in a local JSON file.
    """
    if not settings.SKIP_SUPABASE:
        raise HTTPException(
            status_code=400, 
            detail="Local signup is only available when SKIP_SUPABASE=True"
        )

    # Load existing users
    users = []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                users = json.load(f)
        except json.JSONDecodeError:
            users = []

    # Check if email exists
    if any(u["email"] == request.email for u in users):
        raise HTTPException(status_code=400, detail="User already exists")

    # Create new user
    new_user = {
        "id": str(uuid4()),
        "email": request.email,
        "password": request.password, # Note: Storing plaintext for local dev only!
        "user_metadata": {"full_name": request.full_name},
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    users.append(new_user)

    # Save to file
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

    logger.info(f"New local user registered: {request.email}")
    
    return {
        "message": "User registered successfully", 
        "user": {k:v for k,v in new_user.items() if k != "password"}
    }
