# ensemble_layer/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ensemble_layer.api.ensemble_router import router, registry_router, drift_router

from backend_shared.mlops.retrain_trigger import start_scheduler, stop_scheduler
from backend_shared.registry.model_loader import preload_all_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    preload_all_models()
    start_scheduler()
    print("Models loaded, drift scheduler running.")
    yield
    stop_scheduler()


app = FastAPI(title="Ensemble Layer API", lifespan=lifespan)

app.include_router(router)           # /api/v1/ensemble/...
app.include_router(registry_router)  # /api/v1/registry/...
app.include_router(drift_router)     # /api/v1/drift/...