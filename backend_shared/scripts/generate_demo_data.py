# backend_shared/scripts/generate_demo_data.py
"""Generate comprehensive production-grade demo data for all system features."""
import uuid
import random
import numpy as np
from datetime import datetime, timezone, timedelta
from backend_shared.db.database import get_db_session
from backend_shared.db.models import PredictionLog, VitalSignsHistory

def generate_demo_data():
    """Create realistic demo data showcasing all system capabilities."""
    
    PATIENTS = [
        {"id": "PT-ICU-001", "tier": "CRITICAL", "prob": 0.85, "track": "ensemble_unified"},
        {"id": "PT-ICU-002", "tier": "HIGH", "prob": 0.67, "track": "track1_eicu"},
        {"id": "PT-ICU-003", "tier": "MODERATE", "prob": 0.42, "track": "track2_multimorbidity"},
        {"id": "PT-ICU-004", "tier": "LOW", "prob": 0.12, "track": "track1_eicu"},
        {"id": "PT-ICU-005", "tier": "HIGH", "prob": 0.71, "track": "track3_vitaldb"},
    ]
    
    TRACK_SHAP_TEMPLATES = {
        "track1_eicu": [
            {"feature": "BUN_min", "shap_value": -0.019, "direction": "decreases_risk"},
            {"feature": "TV_max", "shap_value": 0.015, "direction": "increases_risk"},
            {"feature": "lactate_mean", "shap_value": 0.012, "direction": "increases_risk"},
        ],
        "track2_multimorbidity": [
            {"feature": "glucose_mean", "shap_value": 1.0, "direction": "increases_risk"},
            {"feature": "sbp_mean", "shap_value": 0.9, "direction": "increases_risk"},
            {"feature": "map_mean", "shap_value": 0.8, "direction": "increases_risk"},
        ],
        "track3_vitaldb": [],  # No native SHAP
    }
    
    records_created = 0
    
    with get_db_session() as db:
        # ── Generate patient prediction logs with full metadata ──
        for p in PATIENTS:
            ts = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))
            
            # Build realistic track_results based on primary track
            track_results = {}
            if "track1" in p["track"] or p["track"] == "ensemble_unified":
                track_results["track1_eicu"] = {
                    "mortality_probability": round(p["prob"] * 0.9, 4),
                    "risk_tier": p["tier"],
                    "top_shap_drivers": TRACK_SHAP_TEMPLATES["track1_eicu"],
                    "model_version": "track1_random_forest_v1.0",
                }
            if "track2" in p["track"] or p["track"] == "ensemble_unified":
                track_results["track2_multimorbidity"] = {
                    "crisis_probability": round(p["prob"] * 0.85, 4),
                    "severity_level": p["tier"],
                    "shap_top_drivers": ["glucose_mean", "sbp_mean", "map_mean"],
                    "model_version": "v4.0.0",
                }
            if "track3" in p["track"] or p["track"] == "ensemble_unified":
                track_results["track3_vitaldb"] = {
                    "hypotension_probability": round(random.uniform(0.0, 0.3), 4),
                    "tachycardia_probability": round(random.uniform(0.0, 0.4), 4),
                    "low_spo2_probability": round(random.uniform(0.0, 0.2), 4),
                    "risk_level": p["tier"],
                    "model_used": "vitaldb_lstm_v2.1",
                }
            
            # Build prediction_json with SHAP
            top_features = []
            for t_name, t_data in track_results.items():
                if "top_shap_drivers" in t_data:
                    top_features.extend(t_data["top_shap_drivers"])
                elif "shap_top_drivers" in t_data:
                    weight = 1.0
                    for f in t_data["shap_top_drivers"]:
                        top_features.append({"feature": f, "shap_value": round(weight, 4), "direction": "increases_risk"})
                        weight -= 0.1
            
            prediction_json = {
                "risk_score": p["prob"],
                "risk_tier": p["tier"],
                "track_scores": {k: v.get("mortality_probability", v.get("crisis_probability", max(v.get("hypotension_probability", 0), v.get("tachycardia_probability", 0), v.get("low_spo2_probability", 0)))) for k, v in track_results.items()},
                "alert": f"{p['tier']} — Clinical alert for {p['id']}",
                "top_features": top_features[:5],
                "dominant_track": p["track"].replace("_unified", "").split("_")[0] + "_eicu" if "ensemble" in p["track"] else p["track"],
            }
            
            log = PredictionLog(
                request_id=str(uuid.uuid4()),
                patient_id=p["id"],
                track_id=p["track"],
                probability=p["prob"],
                risk_tier=p["tier"],
                features_json={"demo": True},
                latency_ms=round(random.uniform(15, 250), 1),
                model_version="ensemble_v1.0.0",
                timestamp=ts,
                prediction_json=prediction_json,
            )
            db.add(log)
            records_created += 1
        
        db.flush()
        
        # ── Generate vital signs time-series for PT-ICU-001 (CRITICAL patient) ──
        print("Generating vital signs time-series...")
        base_hr, base_map, base_spo2 = 110, 58, 88  # Critical baseline
        for i in range(72):  # 12 hours at 10-min intervals
            ts = datetime.now(timezone.utc) - timedelta(minutes=i * 10)
            # Add realistic deterioration trend
            trend_factor = i / 72.0
            entry = VitalSignsHistory(
                patient_id="PT-ICU-001",
                timestamp=ts,
                hr=round(base_hr + random.gauss(0, 8) + trend_factor * 20, 1),
                map_val=round(base_map + random.gauss(0, 5) - trend_factor * 10, 1),
                spo2=round(min(100, max(75, base_spo2 + random.gauss(0, 2) - trend_factor * 8)), 1),
            )
            db.add(entry)
        records_created += 72
        
        # ── Generate healthy baseline vitals for PT-ICU-004 (LOW risk) ──
        for i in range(72):
            ts = datetime.now(timezone.utc) - timedelta(minutes=i * 10)
            entry = VitalSignsHistory(
                patient_id="PT-ICU-004",
                timestamp=ts,
                hr=round(random.gauss(78, 6), 1),
                map_val=round(random.gauss(82, 5), 1),
                spo2=round(min(100, max(94, random.gauss(97, 1.5))), 1),
            )
            db.add(entry)
        records_created += 72
        
        # ── Generate historical drift baselines (30-60 days ago) ──
        print("Generating drift monitoring baselines...")
        TRACK_BASELINES = {
            "track1_eicu": lambda: {"age": random.randint(55,85), "heartrate_mean": round(random.gauss(88,12),1), "sao2_mean": round(random.gauss(96,2),1), "systemicmean_mean": round(random.gauss(75,8),1), "lactate_mean": round(max(0.5,random.gauss(2.0,0.8)),2), "creatinine_mean": round(max(0.4,random.gauss(1.3,0.5)),2), "glucose_mean": round(max(60,random.gauss(120,35)),1), "temperature_mean": round(random.gauss(37.2,0.6),1)},
            "track2_multimorbidity": lambda: {"glucose_mean": round(max(60,random.gauss(145,40)),1), "glucose_count": random.randint(5,20), "sbp_mean": round(max(80,random.gauss(118,18)),1), "sbp_count": random.randint(20,60), "map_mean": round(max(50,random.gauss(78,10)),1), "map_count": random.randint(20,60)},
            "track3_vitaldb": lambda: {"ECG": round(random.gauss(1.0,0.5),2), "HR": round(max(50,random.gauss(85,15)),1), "MAP": round(max(45,random.gauss(78,12)),1), "SPO2": round(min(100,max(85,random.gauss(96,3))),1)},
        }
        
        for track_id, feat_fn in TRACK_BASELINES.items():
            prob_range = {"track1_eicu": (0.15,0.55), "track2_multimorbidity": (0.05,0.45), "track3_vitaldb": (0.02,0.35)}[track_id]
            tiers = ["LOW", "MODERATE"] if track_id != "track1_eicu" else ["LOW", "MODERATE", "HIGH"]
            
            for i in range(200):
                days_ago = random.randint(30, 60)
                ts = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=random.randint(0,23), minutes=random.randint(0,59))
                
                log = PredictionLog(
                    request_id=str(uuid.uuid4()),
                    patient_id=f"HIST-{track_id[:3].upper()}-{i+1:04d}",
                    track_id=track_id,
                    probability=round(random.uniform(*prob_range), 4),
                    risk_tier=random.choice(tiers),
                    features_json=feat_fn(),
                    latency_ms=round(random.uniform(8, 45), 1),
                    model_version="v4.0.0",
                    timestamp=ts,
                )
                db.add(log)
                records_created += 1
            
            db.flush()
            print(f"  ✅ Added 200 baseline records for {track_id}")
        
        db.commit()
    
    print(f"\n🎉 TOTAL DEMO RECORDS CREATED: {records_created}")
    print("Database is now ready for full-system demonstration!")

if __name__ == "__main__":
    generate_demo_data()