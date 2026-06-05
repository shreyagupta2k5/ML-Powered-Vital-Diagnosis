# backend_shared/mlops/test_drift_monitor.py
"""Smoke tests for drift monitoring service."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from backend_shared.mlops.drift_monitor import compute_psi, compute_ks, check_drift_for_track

def test_psi_ks():
    import numpy as np
    ref = np.random.normal(0, 1, 1000)
    curr_same = np.random.normal(0, 1, 1000)
    curr_drifted = np.random.normal(2, 1, 1000)
    
    psi_same = compute_psi(ref, curr_same)
    psi_drift = compute_psi(ref, curr_drifted)
    _, p_same = compute_ks(ref, curr_same)
    _, p_drift = compute_ks(ref, curr_drifted)
    
    assert psi_same < 0.10, f"PSI should be low for same dist: {psi_same}"
    assert psi_drift > 0.25, f"PSI should be high for drifted dist: {psi_drift}"
    assert p_same > 0.05, f"KS p-value should be high for same dist: {p_same}"
    assert p_drift < 0.05, f"KS p-value should be low for drifted dist: {p_drift}"
    print(" PSI/KS tests passed")

def test_check_drift_for_track():
    # Test with Track 2 (has reference data)
    result = check_drift_for_track("track2_multimorbidity", window_minutes=60)
    assert "track_id" in result
    assert result["track_id"] == "track2_multimorbidity"
    print(f" Drift check for Track 2: status={result['status']}, drifted={result['features_drifted']}")

if __name__ == "__main__":
    test_psi_ks()
    test_check_drift_for_track()
    print("\n All drift monitor tests passed")