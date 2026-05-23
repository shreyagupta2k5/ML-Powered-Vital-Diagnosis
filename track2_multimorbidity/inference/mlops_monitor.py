# ==========================================
# TRACK 2 | MLOPS MONITOR: DRIFT DETECTION & AUTO-RETRAIN
# Author: Swayam (Track 2: Complex Multi-Morbidity Core)
# Objective: Implement continuous learning loop: monitor telemetry logs,
#            detect data drift via PSI/KS, and trigger model retraining.
# ==========================================

import json
import pathlib
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from scipy.stats import ks_2samp
import joblib
import warnings
warnings.filterwarnings('ignore')

# Resolve project root
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

class MLOpsMonitor:
    """
    Monitors inference telemetry for data drift and triggers retraining.
    Runs as async background task in FastAPI app.
    """
    
    def __init__(
        self,
        log_path: pathlib.Path,
        reference_stats_path: pathlib.Path,
        model_path: pathlib.Path,
        output_dir: pathlib.Path,
        psi_threshold: float = 0.25,
        ks_alpha: float = 0.05,
        min_samples_for_drift: int = 50
    ):
        self.log_path = log_path
        self.reference_stats_path = reference_stats_path
        self.model_path = model_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.psi_threshold = psi_threshold
        self.ks_alpha = ks_alpha
        self.min_samples = min_samples_for_drift
        
        # Load reference statistics
        with open(reference_stats_path, 'r') as f:
            self.reference_stats = json.load(f)
        
        # Track current model version
        self.current_model_version = "v1.0.0"
        self.last_drift_check = None
        self.drift_alerts: List[Dict] = []
        
        print(f"MLOps Monitor initialized")
        print(f"  Reference stats: {reference_stats_path.name}")
        print(f"  Drift thresholds: PSI>{psi_threshold}, KS p<{ks_alpha}")
    
    def calculate_psi(self, baseline: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """Calculate Population Stability Index between two distributions."""
        baseline = baseline[~np.isnan(baseline)]
        current = current[~np.isnan(current)]
        
        if len(baseline) < 10 or len(current) < 10:
            return 0.0
        
        # Create bins based on baseline distribution
        min_val = min(baseline.min(), current.min())
        max_val = max(baseline.max(), current.max())
        breakpoints = np.linspace(min_val, max_val, bins + 1)
        
        # Compute histograms
        base_counts, _ = np.histogram(baseline, breakpoints)
        curr_counts, _ = np.histogram(current, breakpoints)
        
        # Convert to proportions with smoothing
        base_dist = (base_counts + 1e-6) / (base_counts.sum() + 1e-6 * bins)
        curr_dist = (curr_counts + 1e-6) / (curr_counts.sum() + 1e-6 * bins)
        
        # Calculate PSI
        psi = np.sum((curr_dist - base_dist) * np.log(curr_dist / base_dist))
        return float(psi)
    
    def ks_test(self, baseline: np.ndarray, current: np.ndarray) -> Tuple[float, float]:
        """Perform Kolmogorov-Smirnov test for distribution shift."""
        stat, p_value = ks_2samp(baseline, current)
        return float(stat), float(p_value)
    
    def load_recent_telemetry(self, hours: int = 24) -> Optional[pd.DataFrame]:
        """Load telemetry logs from last N hours."""
        if not self.log_path.exists():
            return None
        
        df = pd.read_csv(self.log_path)
        
        # Filter by timestamp
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent = df[df['timestamp_utc'] >= cutoff]
        
        return recent if len(recent) >= self.min_samples else None
    
    def scan_drift(self, telemetry_df: pd.DataFrame) -> Dict[str, Dict]:
        """Scan all numeric features for drift using PSI and KS tests."""
        results = {}
        
        # Extract feature columns (exclude metadata)
        feature_cols = [c for c in telemetry_df.columns 
                       if c not in ['timestamp_utc', 'model_version', 'request_id', 
                                   'crisis_probability', 'severity_level', 'crisis_type',
                                   'inference_latency_ms', 'drift_psi_score']]
        
        for feature in feature_cols:
            if feature not in self.reference_stats:
                continue
                
            baseline_stats = self.reference_stats[feature]
            baseline_mean = baseline_stats.get('mean')
            baseline_std = baseline_stats.get('std')
            
            if baseline_mean is None or baseline_std is None:
                continue
            
            # Generate synthetic baseline samples for comparison
            # (In production, store actual baseline samples)
            baseline_samples = np.random.normal(
                baseline_mean, baseline_std, size=1000
            )
            
            current_samples = telemetry_df[feature].dropna().values
            
            if len(current_samples) < 10:
                continue
            
            # Calculate metrics
            psi = self.calculate_psi(baseline_samples, current_samples)
            ks_stat, p_value = self.ks_test(baseline_samples, current_samples)
            
            # Determine drift
            drift_detected = psi > self.psi_threshold or p_value < self.ks_alpha
            
            results[feature] = {
                'psi': round(psi, 4),
                'ks_stat': round(ks_stat, 4),
                'p_value': round(p_value, 6),
                'drift_detected': drift_detected,
                'sample_size': len(current_samples)
            }
        
        return results
    
    def trigger_retrain(self, drift_report: Dict) -> bool:
        """
        Trigger model retraining when drift is detected.
        In production: queue retraining job, validate new model, hot-swap.
        For prototype: simulate retraining by saving new version metadata.
        """
        drifted_features = [f for f, r in drift_report.items() if r['drift_detected']]
        
        if not drifted_features:
            return False
        
        print(f"\n🚨 DRIFT DETECTED in features: {drifted_features}")
        print("Initiating auto-retrain protocol...")
        
        # Simulate retraining (in production: load new data, fine-tune model)
        new_version = f"v1.{int(self.current_model_version.split('.')[1]) + 1}.0"
        retrain_metadata = {
            'trigger_timestamp': datetime.now(timezone.utc).isoformat(),
            'drifted_features': drifted_features,
            'drift_report': drift_report,
            'new_model_version': new_version,
            'status': 'retraining_simulated'
        }
        
        # Save retrain event
        output_path = self.output_dir / f'retrain_event_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_path, 'w') as f:
            json.dump(retrain_metadata, f, indent=2)
        
        # Update current version (hot-swap simulation)
        self.current_model_version = new_version
        self.drift_alerts.append(retrain_metadata)
        
        print(f"✅ Auto-retrain complete. New model version: {new_version}")
        return True
    
    async def monitor_loop(self, check_interval_minutes: int = 60):
        """Async background task: periodically check for drift and retrain if needed."""
        print(f"\n🔄 Starting MLOps monitor loop (check every {check_interval_minutes} min)")
        
        while True:
            try:
                # Load recent telemetry
                telemetry = self.load_recent_telemetry(hours=24)
                
                if telemetry is not None:
                    print(f"\n🔍 Scanning drift on {len(telemetry)} recent inferences...")
                    
                    # Scan for drift
                    drift_report = self.scan_drift(telemetry)
                    
                    # Log summary
                    drifted = [f for f, r in drift_report.items() if r['drift_detected']]
                    print(f"  Features scanned: {len(drift_report)}")
                    print(f"  Drift detected: {len(drifted)} features")
                    
                    if drifted:
                        print(f"  Drifted features: {drifted}")
                    
                    # Trigger retrain if needed
                    if drifted:
                        self.trigger_retrain(drift_report)
                    
                    # Update last check time
                    self.last_drift_check = datetime.now(timezone.utc)
                
                else:
                    print(f"\n⏳ Insufficient telemetry data for drift check (need ≥{self.min_samples} samples)")
                
                # Wait for next check
                await asyncio.sleep(check_interval_minutes * 60)
                
            except Exception as e:
                print(f"❌ MLOps monitor error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 min before retry
    
    def get_drift_status(self) -> Dict:
        """Return current drift status for /health endpoint."""
        return {
            'last_check': self.last_drift_check.isoformat() if self.last_drift_check else None,
            'current_model_version': self.current_model_version,
            'total_alerts': len(self.drift_alerts),
            'recent_alerts': self.drift_alerts[-5:],  # Last 5 alerts
            'psi_threshold': self.psi_threshold,
            'ks_alpha': self.ks_alpha
        }