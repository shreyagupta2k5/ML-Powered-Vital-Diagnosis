# backend_main/api/vitals_router.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from backend_shared.db.database import get_db_session
from backend_shared.db.models import VitalSignsHistory
from sqlalchemy import desc

router = APIRouter(prefix="/api/v1/patient", tags=["Patient Vitals"])

class VitalSignPoint(BaseModel):
    timestamp: str
    hr: Optional[float]
    map_val: Optional[float]
    spo2: Optional[float]

@router.get("/{patient_id}/vitals", response_model=List[VitalSignPoint])
async def get_patient_vitals(
    patient_id: str,
    range: str = Query(default="6h", description="Time range: 1h, 6h, 24h")
):
    """Retrieve time-series vital signs for a patient over the specified range."""
    range_map = {"1h": 60, "6h": 360, "24h": 1440}
    minutes = range_map.get(range, 360)
    
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    try:
        with get_db_session() as db:
            rows = (
                db.query(VitalSignsHistory)
                .filter(
                    VitalSignsHistory.patient_id == patient_id,
                    VitalSignsHistory.timestamp >= cutoff
                )
                .order_by(desc(VitalSignsHistory.timestamp))
                .all()
            )
            
            return [
                VitalSignPoint(
                    timestamp=row.timestamp.isoformat(),
                    hr=row.hr,
                    map_val=row.map_val,
                    spo2=row.spo2,
                )
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve vitals: {str(e)}")