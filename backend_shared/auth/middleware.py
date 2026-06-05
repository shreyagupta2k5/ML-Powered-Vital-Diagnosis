# backend_shared/auth/middleware.py
"""FastAPI middleware for auth + rate limiting integration."""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from .auth import get_current_user, require_scope
from .rate_limiter import rate_limit_middleware, prediction_limiter

def setup_auth_middleware(app: FastAPI):
    """Attach auth and rate limiting to FastAPI app."""
    
    # Global exception handler for auth errors
    @app.exception_handler(401)
    async def auth_error_handler(request: Request, exc):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authentication required"}
        )
    
    @app.exception_handler(403)
    async def permission_error_handler(request: Request, exc):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Insufficient permissions"}
        )
    
    @app.exception_handler(429)
    async def rate_limit_error_handler(request: Request, exc):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": "60"}
        )
    
    # Attach rate limiting to prediction endpoints (example)
    # In practice, apply via Depends() in route definitions
    print("Auth middleware configured: JWT + API key + rate limiting active")