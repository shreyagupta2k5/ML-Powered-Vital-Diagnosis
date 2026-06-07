# backend_tests/test_performance.py
import pytest
import httpx
import time
import statistics

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_track2_latency():
    """Ensure Track 2 prediction is under 200ms."""
    payload = {"glucose_mean": 145.0, "glucose_count": 10.0, "sbp_mean": 135.0, "sbp_count": 50.0, "map_mean": 95.0, "map_count": 50.0}
    
    latencies = []
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        for _ in range(10):
            start = time.perf_counter()
            await client.post("/api/v1/track2/predict", json=payload)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
            
    p95 = statistics.quantiles(latencies, n=20)[18] # Approximate p95
    print(f"Track 2 P95 Latency: {p95:.2f}ms")
    assert p95 < 200, f"Latency too high: {p95:.2f}ms"

@pytest.mark.asyncio
async def test_ensemble_latency():
    """Ensure Ensemble prediction is under 500ms."""
    payload = {
        "patient_id": "PERF_TEST",
        "track1_features": {"age": 55, "gender": "Male", "admissionweight": 75.0, "heartrate_mean": 85.0, "heartrate_min": 78.0, "heartrate_max": 92.0, "heartrate_std": 4.0, "heartrate_count": 24, "respiration_mean": 16.0, "sao2_mean": 98.0, "sao2_min": 96.0, "temperature_mean": 36.9, "systemicmean_mean": 75.0, "systemicmean_min": 68.0, "systemicmean_max": 84.0, "systemicmean_std": 5.0, "lactate_mean": 1.2, "creatinine_mean": 0.9, "glucose_mean": 120.0},
        "track2_features": {"glucose_mean": 120, "glucose_count": 5, "sbp_mean": 118, "sbp_count": 4, "map_mean": 75, "map_count": 3},
        "track3_features": {"mean_hr": 85, "std_hr": 4, "min_hr": 78, "max_hr": 92, "mean_map": 75, "std_map": 5, "min_map": 68, "max_map": 84, "map_range": 16, "mean_spo2": 98, "std_spo2": 1, "min_spo2": 96, "mean_ecg": 0.12, "std_ecg": 0.05, "min_ecg": -0.2, "max_ecg": 0.4, "map_variability": 5, "hr_variability": 4, "ecg_range": 0.6, "map_drop": 16, "spo2_drop": 2}
    }
    
    latencies = []
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        for _ in range(10):
            start = time.perf_counter()
            await client.post("/api/v1/ensemble/predict", json=payload)
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
            
    p95 = statistics.quantiles(latencies, n=20)[18]
    print(f"Ensemble P95 Latency: {p95:.2f}ms")
    assert p95 < 500, f"Ensemble latency too high: {p95:.2f}ms"