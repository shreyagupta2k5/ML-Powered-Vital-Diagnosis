from fastapi import FastAPI

from track3_vitalDB.backend.api.vitaldb_router import router

app = FastAPI(
    title="Track 3 VitalDB API"
)

app.include_router(router)