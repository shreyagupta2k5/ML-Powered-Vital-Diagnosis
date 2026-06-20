# backend_main/api/history_router.py
"""
History Router — Task 6.1 Fix 1
Provides a lightweight endpoint to fetch recent patient predictions for the dashboard.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any 
from datetime import datetime
from pydantic import BaseModel

from backend_shared.db.database import get_db_session
from backend_shared.db.models import PredictionLog
from sqlalchemy import func, desc

router = APIRouter(prefix="/api/v1", tags=["Patient History"])

class PatientHistoryItem(BaseModel):
    patient_id: str
    last_risk_tier: str
    last_probability: float
    last_timestamp: datetime
    track_id: str
    prediction_json: Optional[Dict[str, Any]] = None
    features_json: Optional[Dict[str, Any]] = None  

@router.get("/history", response_model=List[PatientHistoryItem])
async def get_patient_history(limit: int = 50):
    """
    Retrieve the most recent prediction for each unique patient.
    Useful for populating the main dashboard table without re-running inference.
    """
    try:
        with get_db_session() as db:
            # Subquery to find the latest log ID for each patient
            subquery = (
                db.query(
                    PredictionLog.patient_id,
                    func.max(PredictionLog.id).label("max_id")
                )
                .filter(PredictionLog.patient_id.isnot(None))
                .group_by(PredictionLog.patient_id)
                .subquery()
            )
            
            # Join back to get the full record details
            results = (
                db.query(PredictionLog)
                .join(subquery, PredictionLog.id == subquery.c.max_id)
                .order_by(desc(PredictionLog.timestamp))
                .limit(limit)
                .all()
            )
            
            history = []
            for log in results:
                # Explicitly access attributes INSIDE the session to ensure they are loaded
                history.append(PatientHistoryItem(
                    patient_id=str(log.patient_id),
                    last_risk_tier=str(log.risk_tier),
                    last_probability=float(log.probability),
                    last_timestamp=log.timestamp,
                    track_id=str(log.track_id),
                    prediction_json=log.prediction_json,
                    features_json=log.features_json 
                ))
                
            return history
            
    except Exception as e:
        print(f"History Endpoint Error: {e}") # Debug print
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patient history: {str(e)}"
        )