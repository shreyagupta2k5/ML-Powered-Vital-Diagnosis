"""
Smoke-test for model_loader — run from repo root:
  python test_loader.py
"""
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from backend_shared.registry.model_loader import (
    preload_all_models,
    list_loaded,
    get_loaded_model_meta,
    load_model,
)

print("\n" + "=" * 55)
print("MODEL LOADER SMOKE TEST")
print("=" * 55)

results = preload_all_models()

print("\nResults:")
for track, ok in results.items():
    status = "OK" if ok else "FAILED"
    meta   = get_loaded_model_meta(track) if ok else {}
    version = meta.get("version", "-") if meta else "-"
    mtype   = meta.get("model_type", "-") if meta else "-"
    print(f"  {track:<30} {status}   version={version}  type={mtype}")

print(f"\nLoaded tracks : {list_loaded()}")

# Quick type check for track3 ensemble
if results.get("track3_vitaldb"):
    t3 = load_model("track3_vitaldb")
    print(f"\ntrack3 events : {list(t3.keys())}")
    for event, bundle in t3.items():
        print(f"  {event}: model={type(bundle['model']).__name__}, scaler={type(bundle['scaler']).__name__ if bundle['scaler'] else 'None'}")

print("\n" + "=" * 55)