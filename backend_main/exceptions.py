# backend_main/exceptions.py
from fastapi import HTTPException, status

class InvalidFeatureError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

class ModelNotFoundError(HTTPException):
    def __init__(self, track_id: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Model for {track_id} is not loaded or found."
        )

class DriftDetectedError(HTTPException):
    def __init__(self, feature_name: str, psi_score: float):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT, 
            detail=f"Significant drift detected in '{feature_name}' (PSI={psi_score}). Prediction blocked pending retrain."
        )

class RateLimitExceededError(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
            detail="Rate limit exceeded.",
            headers={"Retry-After": str(retry_after)}
        )