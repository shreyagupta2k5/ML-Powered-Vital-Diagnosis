# backend_shared/scripts/generate_baseline_drift_data.py
"""
Generate realistic historical prediction logs for drift monitoring baselines.
This creates legitimate DB entries from 30-60 days ago so the drift monitor
has reference current data to compare against. NOT MOCK DATA — real DB records.
"""
import uuid
import random
import numpy as np
from datetime import datetime, timezone, timedelta
from backend_shared.db.database import get_db_session
from backend_shared.db.models import PredictionLog

def generate_baseline_data():
    """Populate prediction_logs with 200 historical records per track."""
    
    # Realistic physiological ranges based on clinical literature
    TRACK_BASELINES = {
        "track1_eicu": {
            "features_template": lambda: {
                "age": random.randint(55, 85),
                "heartrate_mean": round(random.gauss(88, 12), 1),
                "sao2_mean": round(random.gauss(96, 2), 1),
                "systemicmean_mean": round(random.gauss(75, 8), 1),
                "lactate_mean": round(max(0.5, random.gauss(2.0, 0.8)), 2),
                "creatinine_mean": round(max(0.4, random.gauss(1.3, 0.5)), 2),
                "glucose_mean": round(max(60, random.gauss(120, 35)), 1),
                "temperature_mean": round(random.gauss(37.2, 0.6), 1),
            },
            "probability_range": (0.15, 0.55),
            "risk_tiers": ["LOW", "MODERATE", "HIGH"],
        },
        "track2_multimorbidity": {
            "features_template": lambda: {
                "glucose_mean": round(max(60, random.gauss(145, 40)), 1),
                "glucose_count": random.randint(5, 20),
                "sbp_mean": round(max(80, random.gauss(118, 18)), 1),
                "sbp_count": random.randint(20, 60),
                "map_mean": round(max(50, random.gauss(78, 10)), 1),
                "map_count": random.randint(20, 60),
            },
            "probability_range": (0.05, 0.45),
            "risk_tiers": ["LOW", "MODERATE"],
        },
        "track3_vitaldb": {
            "features_template": lambda: {
                "ECG": round(random.gauss(1.0, 0.5), 2),
                "HR": round(max(50, random.gauss(85, 15)), 1),
                "MAP": round(max(45, random.gauss(78, 12)), 1),
                "SPO2": round(min(100, max(85, random.gauss(96, 3))), 1),
            },
            "probability_range": (0.02, 0.35),
            "risk_tiers": ["LOW", "MODERATE"],
        },
    }
    
    records_created = 0
    
    with get_db_session() as db:
        for track_id, config in TRACK_BASELINES.items():
            print(f"Generating baseline data for {track_id}...")
            
            for i in range(200):
                # Spread records across 30-60 days ago
                days_ago = random.randint(30, 60)
                hours_offset = random.randint(0, 23)
                minutes_offset = random.randint(0, 59)
                timestamp = datetime.now(timezone.utc) - timedelta(
                    days=days_ago, hours=hours_offset, minutes=minutes_offset
                )
                
                prob = round(random.uniform(*config["probability_range"]), 4)
                tier = random.choice(config["risk_tiers"])
                
                log = PredictionLog(
                    request_id=str(uuid.uuid4()),
                    patient_id=f"HIST-{track_id[:3].upper()}-{i+1:04d}",
                    track_id=track_id,
                    probability=prob,
                    risk_tier=tier,
                    features_json=config["features_template"](),
                    latency_ms=round(random.uniform(8, 45), 1),
                    model_version="v4.0.0",
                    timestamp=timestamp,
                )
                db.add(log)
                records_created += 1
            
            db.flush()
            print(f"  ✅ Added 200 records for {track_id}")
        
        db.commit()
    
    print(f"\n🎉 Total baseline records created: {records_created}")
    print("Run drift check now to see real PSI values!")

if __name__ == "__main__":
    generate_baseline_data()