# backend_main/dependencies.py
from typing import Optional, Union
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend_shared.auth.auth import get_current_user, TokenData, APIKeyData
from backend_shared.auth.rate_limiter import default_limiter, prediction_limiter, rate_limit_middleware

security = HTTPBearer(auto_error=False)

async def get_api_key_header(x_api_key: Optional[str] = None) -> Optional[str]:
    """Extract API key from header."""
    return x_api_key

async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_key: Optional[str] = Depends(get_api_key_header)
) -> Union[TokenData, APIKeyData]:
    """
    Dependency to enforce authentication via JWT or API Key.
    Usage: dependencies=[Depends(require_auth)]
    """
    return await get_current_user(credentials, api_key)

async def rate_limit_default(request: Request):
    """Default rate limiter (e.g., 100 req/min)."""
    return await rate_limit_middleware(request, limiter=default_limiter)

async def rate_limit_prediction(request: Request):
    """Stricter rate limiter for prediction endpoints (e.g., 10 req/min)."""
    return await rate_limit_middleware(request, limiter=prediction_limiter)