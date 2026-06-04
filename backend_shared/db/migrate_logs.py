# backend_shared/db/migrate_logs.py
"""Migration script to import existing CSV logs into the database."""
import csv
import pathlib
from datetime import datetime
from .database import init_db, get_db_session
from .models import PredictionLog, DriftMetric

def migrate_track2_logs(csv_path: pathlib.Path) -> int:
    """Migrate Track 2 telemetry logs to database."""
    if not csv_path.exists():
        return 0
    
    count = 0
    with get_db_session() as db:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    entry = PredictionLog(
                        request_id=row.get('request_id', ''),
                        patient_id=row.get('patient_id'),
                        timestamp=datetime.fromisoformat(row['timestamp_utc']),
                        track_id='track2_multimorbidity',
                        probability=float(row.get('crisis_probability', 0)),
                        risk_tier=row.get('severity_level', 'UNKNOWN'),
                        latency_ms=float(row.get('inference_latency_ms', 0))
                    )
                    db.add(entry)
                    count += 1
                except Exception:
                    continue
        db.commit()
    return count

def migrate_all() -> None:
    """Run all available migrations."""
    print("Initializing database tables...")
    init_db()
    
    project_root = pathlib.Path(__file__).resolve().parent.parent.parent
    
    # Migrate Track 2 logs (example)
    track2_csv = project_root / "track2_multimorbidity" / "inference" / "logs" / "api_inference_logs.csv"
    if track2_csv.exists():
        n = migrate_track2_logs(track2_csv)
        print(f"Migrated {n} records from Track 2")
    else:
        print("Track 2 log file not found")
    
    # Add Track 1 & Track 3 migration calls here when their CSV formats are finalized
    print("Migration complete.")

if __name__ == "__main__":
    migrate_all()