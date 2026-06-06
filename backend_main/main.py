# backend_main/main.py
import datetime
import httpx
import asyncio
from fastapi import FastAPI, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend_main.auth_router import router as auth_router
from backend_main.websockets.alert_stream import router as ws_router
from backend_main.websockets.alert_stream import alert_worker

import warnings
from sklearn.exceptions import (
    InconsistentVersionWarning
)

warnings.filterwarnings(
    "ignore",
    category=InconsistentVersionWarning
)

import joblib

from backend_main.config import settings
from backend_main.dependencies import rate_limit_default

# Import routers from individual tracks and ensemble layer
from track1_eicu_pipeline.api.eicu_router import router as track1_router
from track2_multimorbidity.api.track2_router import router as track2_router
from track3_vitalDB.backend.api.vitaldb_router import router as track3_router
from ensemble_layer.api.ensemble_router import (
    router as ensemble_router,
    registry_router,
    drift_router
)

from backend_main.websockets.alert_stream import router as websocket_router

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# =============================================================================
# GLOBAL MIDDLEWARE
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# GLOBAL EXCEPTION HANDLERS
# =============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."}
    )

@app.exception_handler(401)
async def auth_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Authentication required. Provide a valid JWT or API Key."},
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.exception_handler(403)
async def permission_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "Insufficient permissions for this resource."}
    )

@app.exception_handler(429)
async def rate_limit_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Rate limit exceeded. Please slow down."},
        headers={"Retry-After": "60"}
    )

# =============================================================================
# ROUTER INCLUSION
# =============================================================================
# Note: Individual routers already have their own prefixes defined in their respective files.
# We include them here to mount them to the main app.
app.include_router(track1_router)
app.include_router(track2_router)
app.include_router(track3_router)
app.include_router(ensemble_router)
app.include_router(registry_router)
app.include_router(drift_router)
app.include_router(auth_router)
app.include_router(ws_router)

# =============================================================================
# STARTUP EVENTS
# =============================================================================
@app.on_event("startup")
async def startup_websocket_worker():
    """Start the WebSocket background worker (must be on the main app)."""
    asyncio.create_task(alert_worker())
    print(" WebSocket alert worker started.")

# =============================================================================
# CORE ENDPOINTS
# =============================================================================
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint providing API documentation links."""
    return {
        "message": "Welcome to the ML-Powered Vital Diagnosis API",
        "version": settings.APP_VERSION,
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "health_check": "/health",
        "available_tracks": [
            "/api/v1/track1",
            "/api/v1/track2",
            "/api/v1/track3",
            "/api/v1/ensemble"
        ]
    }

@app.get("/health", tags=["System"], dependencies=[Depends(rate_limit_default)])
async def health_check():
    """
    Aggregated health check endpoint.
    Pings all individual track services to ensure the entire ecosystem is healthy.
    """
    health_status = {
        "status": "healthy",
        "service": "backend_main",
        "tracks": {},
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    
    track_urls = {
        "track1_eicu": f"{settings.TRACK1_URL}/api/v1/track1/health",
        "track2_multimorbidity": f"{settings.TRACK2_URL}/api/v1/track2/health",
        "track3_vitaldb": f"{settings.TRACK3_URL}/api/v1/track3/health",
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in track_urls.items():
            try:
                response = await client.get(url)
                health_status["tracks"][name] = "healthy" if response.status_code == 200 else "unhealthy"
            except httpx.RequestError:
                health_status["tracks"][name] = "unreachable"
            except Exception:
                health_status["tracks"][name] = "error"
                
    # Determine overall system status
    if any(status in ["unhealthy", "unreachable", "error"] for status in health_status["tracks"].values()):
        health_status["status"] = "degraded"
        
    return health_status
