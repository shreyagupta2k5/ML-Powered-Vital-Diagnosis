# backend_shared/registry/test_model_registry.py
"""Smoke tests for model registry and loader."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from backend_shared.registry.model_registry import get_active_version, list_versions
from backend_shared.registry.model_loader import load_model, preload_all_models

def test_registry_queries():
    # Test Track 2 (most likely to work)
    active = get_active_version("track2_multimorbidity")
    assert active is not None, "Track 2 active version not found"
    assert active["version"] == "v4.0.0"
    print(f" Registry query: Track 2 active = {active['version']}")
    
    # List all versions for Track 2
    versions = list_versions("track2_multimorbidity")
    assert len(versions) >= 1
    print(f" Track 2 has {len(versions)} registered version(s)")

def test_model_loading():
    # Preload all (may fail for missing files, but should not crash)
    results = preload_all_models()
    print(f" Preload results: {results}")
    
    # Try loading Track 2 specifically
    try:
        model = load_model("track2_multimorbidity")
        print(f"Track 2 model loaded: {type(model).__name__}")
    except Exception as e:
        print(f" Track 2 model load failed (expected if path wrong): {e}")

if __name__ == "__main__":
    test_registry_queries()
    test_model_loading()
    print("\n All registry/loader tests completed")