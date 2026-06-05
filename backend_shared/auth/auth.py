# backend_shared/auth/auth.py
"""JWT-based authentication with API key fallback."""
import os
import jwt
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Union
from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# JWT Configuration (loaded from env)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-prod")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
API_KEYS = os.getenv("API_KEYS", "dev-api-key").split(",")

security = HTTPBearer(auto_error=False)

class TokenData(BaseModel):
    user_id: Optional[str] = None
    scopes: list[str] = []

class APIKeyData(BaseModel):
    key_id: str
    scopes: list[str] = []

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        scopes = payload.get("scopes", [])
        return TokenData(user_id=user_id, scopes=scopes)
    except jwt.PyJWTError:
        return None

def verify_api_key(api_key: str) -> Optional[APIKeyData]:
    """Verify a static API key."""
    if api_key in API_KEYS:
        return APIKeyData(key_id=f"key_{hash(api_key) % 1000}", scopes=["read", "write"])
    return None

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    api_key: Optional[str] = None
) -> Union[TokenData, APIKeyData]:
    """
    Authenticate request via JWT Bearer token OR API key.
    Raises HTTPException if neither is valid.
    """
    # Try JWT first
    if credentials and credentials.credentials:
        token_data = decode_access_token(credentials.credentials)
        if token_data:
            return token_data
    
    # Fallback to API key
    if api_key:
        key_data = verify_api_key(api_key)
        if key_data:
            return key_data
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_scope(required_scope: str):
    """Dependency factory to require a specific scope."""
    async def scope_checker(user: Union[TokenData, APIKeyData] = Security(get_current_user)):
        if required_scope not in user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required scope: {required_scope}"
            )
        return user
    return scope_checker