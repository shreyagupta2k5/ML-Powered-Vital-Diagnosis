# backend_main/auth_router.py
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from backend_shared.auth.auth import create_access_token, API_KEYS
from backend_main.config import settings
from backend_main.dependencies import require_auth

router = APIRouter(prefix="/auth", tags=["Authentication"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

@router.post("/token", response_model=TokenResponse, summary="Get JWT Access Token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate and get a JWT token.
    For development, use:
    - Username: `admin`, Password: `admin`
    - OR use any configured API Key as the password (e.g., Password: `dev-api-key`)
    """
    valid_dev_users = {"admin": "admin", "demo": "demo"}
    
    # Allow valid dev users OR any valid API key
    if form_data.password in API_KEYS:
        username = form_data.username or "api_client"
    elif valid_dev_users.get(form_data.username) == form_data.password:
        username = form_data.username
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "scopes": ["read", "write", "predict"]},
        expires_delta=access_token_expires
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/validate", summary="Validate Token")
async def validate_token(user=Depends(require_auth)):
    """Check if the current token is valid and return user info."""
    user_id = getattr(user, 'user_id', None) or getattr(user, 'key_id', 'unknown')
    scopes = getattr(user, 'scopes', [])
    return {"status": "valid", "user": user_id, "scopes": scopes}