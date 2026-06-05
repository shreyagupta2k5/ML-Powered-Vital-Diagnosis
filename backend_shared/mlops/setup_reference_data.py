# setup_reference_data.py
"""
One-time setup script — run this after cloning the repo.
Generates reference and current data files needed for drift monitoring.
Run from project root: python setup_reference_data.py
"""
import pandas as pd
import pathlib
import glob

out = pathlib.Path('backend_shared/mlops/reference')
out.mkdir(parents=True, exist_ok=True)

print("Generating drift reference data...")

# Track 1
p1 = pathlib.Path('track1_eicu_pipeline/logs/predictions.csv')
if p1.exists():
    df = pd.read_csv(p1).select_dtypes(include='number')
    df.to_csv(out / 'track1_eicu_reference.csv', index=False)
    df.to_csv(out / 'track1_eicu_current.csv', index=False)
    print(f"Track1: saved {len(df)} rows, {len(df.columns)} cols")
else:
    print("Track1: predictions.csv not found — skipping")

# Track 2
p2 = pathlib.Path('track2_multimorbidity/inference/logs/api_inference_logs.csv')
if p2.exists():
    df = pd.read_csv(p2, on_bad_lines='skip').select_dtypes(include='number')
    df.to_csv(out / 'track2_multimorbidity_reference.csv', index=False)
    df.to_csv(out / 'track2_multimorbidity_current.csv', index=False)
    print(f"Track2: saved {len(df)} rows, {len(df.columns)} cols")
else:
    print("Track2: api_inference_logs.csv not found — skipping")

# Track 3
files = glob.glob('vitalDB project/data/windowed/**/*.csv', recursive=True)
if files:
    dfs = [pd.read_csv(f) for f in files[:100]]
    df = pd.concat(dfs, ignore_index=True).select_dtypes(include='number')
    df.to_csv(out / 'track3_vitaldb_reference.csv', index=False)
    dfs2 = [pd.read_csv(f) for f in files[:50]]
    df2 = pd.concat(dfs2, ignore_index=True).select_dtypes(include='number')
    df2.to_csv(out / 'track3_vitaldb_current.csv', index=False)
    print(f"Track3: saved {len(df)} rows, {len(df.columns)} cols")
else:
    print("Track3: no windowed CSV files found — skipping")

print("\nDone! Reference files saved to backend_shared/mlops/reference/")
print("You can now run: python backend_shared/mlops/retrain_trigger.py once")