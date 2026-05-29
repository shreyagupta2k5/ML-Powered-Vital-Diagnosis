# ==========================================
# TRACK 2 | DRIFT SIMULATION & STRESS TESTING
# Author: Swayam (Track 2: Complex Multi-Morbidity Core)
# Objective: Validate MLOps monitor by injecting synthetic drifted data
#            into telemetry logs and verifying auto-retrain triggers.
# ==========================================

import json
import pathlib
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from track2_multimorbidity.inference.mlops_monitor import MLOpsMonitor

def generate_synthetic_telemetry(
    base_stats: dict,
    n_samples: int = 100,
    drift_feature: str = "glucose_mean",
    drift_magnitude: float = 2.0
) -> pd.DataFrame:
    """Generate synthetic telemetry data with controlled drift in one feature."""
    records = []
    base_mean = base_stats[drift_feature]["mean"]
    base_std = base_stats[drift_feature]["std"]
    
    drifted_mean = base_mean + (drift_magnitude * base_std)
    drifted_std = base_std * drift_magnitude
    
    for i in range(n_samples):
        record = {}
        for feature, stats in base_stats.items():
            if feature == drift_feature:
                value = np.random.normal(drifted_mean, drifted_std)
            else:
                value = np.random.normal(stats["mean"], stats["std"])
            record[feature] = float(np.clip(value, 0, None))
        
        record["timestamp_utc"] = (datetime.now(timezone.utc) - timedelta(hours=np.random.randint(0, 24))).isoformat()
        record["model_version"] = "v1.0.0"
        record["request_id"] = f"synthetic_{i}"
        record["crisis_probability"] = np.random.uniform(0, 1)
        record["severity_level"] = np.random.choice(["LOW", "MODERATE", "HIGH"])
        record["crisis_type"] = "synthetic_drift_test"
        record["inference_latency_ms"] = np.random.uniform(10, 100)
        record["drift_psi_score"] = None
        
        records.append(record)
    
    return pd.DataFrame(records)

def run_drift_simulation(
    log_path: pathlib.Path,
    reference_stats_path: pathlib.Path,
    output_dir: pathlib.Path,
    drift_feature: str = "glucose_mean",
    drift_magnitude: float = 2.0,
    psi_threshold: float = 0.25,
    ks_alpha: float = 0.05
) -> dict:
    """Run end-to-end drift simulation and return results."""
    
    # Load reference stats
    with open(reference_stats_path, 'r') as f:
        reference_stats = json.load(f)
    
    # Ensure drift_feature exists in reference stats
    if drift_feature not in reference_stats["feature_statistics"]:
        available = list(reference_stats["feature_statistics"].keys())
        print(f"Warning: '{drift_feature}' not in reference stats. Using first available: {available[0]}")
        drift_feature = available[0]
    
    print(f"Generating {drift_magnitude}x drift in feature: {drift_feature}")
    synthetic_df = generate_synthetic_telemetry(
        reference_stats["feature_statistics"],
        n_samples=100,
        drift_feature=drift_feature,
        drift_magnitude=drift_magnitude
    )
    
    # Append to telemetry log
    if log_path.exists():
        existing_df = pd.read_csv(log_path)
        combined_df = pd.concat([existing_df, synthetic_df], ignore_index=True)
        combined_df.to_csv(log_path, index=False)
        print(f"Appended {len(synthetic_df)} synthetic records to {log_path}")
    else:
        synthetic_df.to_csv(log_path, index=False)
        print(f"Created new telemetry log with {len(synthetic_df)} synthetic records")
    
    # Initialize monitor
    monitor = MLOpsMonitor(
        log_path=log_path,
        reference_stats_path=reference_stats_path,
        model_path=pathlib.Path("/dev/null"),
        output_dir=output_dir,
        psi_threshold=psi_threshold,
        ks_alpha=ks_alpha,
        min_samples_for_drift=50
    )
    
    # Scan for drift
    drift_report = monitor.scan_drift(synthetic_df)
    
    # Debug: print scanned features
    print(f"\nDrift report scanned {len(drift_report)} features:")
    for feat, metrics in list(drift_report.items())[:5]:  # Show first 5
        print(f"  {feat}: PSI={metrics.get('psi')}, p={metrics.get('p_value')}")
    
    # Get target result with safe access
    target_result = drift_report.get(drift_feature, {})
    drift_detected = target_result.get("drift_detected", False)
    
    # Trigger retrain if drift detected
    retrain_triggered = False
    if drift_detected:
        retrain_triggered = monitor.trigger_retrain(drift_report)
    
    return {
        "drift_feature": drift_feature,
        "drift_magnitude": drift_magnitude,
        "psi_threshold": psi_threshold,
        "ks_alpha": ks_alpha,
        "samples_injected": len(synthetic_df),
        "drift_detected": drift_detected,
        "psi_score": target_result.get("psi"),
        "ks_pvalue": target_result.get("p_value"),
        "retrain_triggered": retrain_triggered,
        "full_report": drift_report
    }

if __name__ == "__main__":
    LOG_PATH = PROJECT_ROOT / "track2_multimorbidity" / "inference" / "logs" / "api_inference_logs.csv"
    REF_STATS_PATH = PROJECT_ROOT / "track2_multimorbidity" / "schema" / "reference_stats.json"
    OUTPUT_DIR = PROJECT_ROOT / "track2_multimorbidity" / "inference" / "retrain_events"
    
    print("Running drift simulation stress test...")
    result = run_drift_simulation(
        log_path=LOG_PATH,
        reference_stats_path=REF_STATS_PATH,
        output_dir=OUTPUT_DIR,
        drift_feature="glucose_mean",
        drift_magnitude=2.0
    )
    
    print("\n" + "="*60)
    print("DRIFT SIMULATION RESULTS")
    print("="*60)
    print(f"Feature tested: {result['drift_feature']}")
    print(f"Drift magnitude: {result['drift_magnitude']}x std")
    
    # Safe formatting for None values
    psi_score = result['psi_score']
    ks_pvalue = result['ks_pvalue']
    print(f"PSI score: {psi_score if psi_score is not None else 'N/A'} (threshold: {result['psi_threshold']})")
    print(f"KS p-value: {ks_pvalue if ks_pvalue is not None else 'N/A'} (alpha: {result['ks_alpha']})")
    print(f"Drift detected: {result['drift_detected']}")
    print(f"Retrain triggered: {result['retrain_triggered']}")
    
    if result['drift_detected'] and result['retrain_triggered']:
        print("\n✅ SUCCESS: Drift simulation validated auto-retrain logic")
    elif result['drift_detected']:
        print("\n⚠️ PARTIAL: Drift detected but retrain not triggered (check thresholds)")
    else:
        print("\n❌ FAILURE: Drift not detected (may need larger magnitude or more samples)")
    
    # Save detailed report
    report_path = OUTPUT_DIR / f"drift_simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nDetailed report saved: {report_path}")