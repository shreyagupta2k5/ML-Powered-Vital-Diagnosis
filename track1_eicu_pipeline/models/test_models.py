# test_models.py
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))

import numpy as np
import pandas as pd
import joblib

print("=" * 50)
print("TESTING SAVED MODELS")
print("=" * 50)

models_dir = pathlib.Path("models")
artifacts_dir = pathlib.Path("artifacts")

# ─────────────────────────────────────────
# Step 1: Check all model files exist
# ─────────────────────────────────────────
print("\n--- Checking model files ---")

expected_models = [
    "track3_best_model.pkl",
    "track3_random_forest.pkl",
    "track3_xgboost.pkl",
    "track3_logistic_regression.pkl",
    "track3_xgboost_smote.pkl",
    "track3_best_model_smote.pkl",
    "track3_rf_calibrated.pkl",
    "track3_xgb_calibrated.pkl",
    "track3_full_pipeline.joblib",
]

for m in expected_models:
    path = models_dir / m
    if path.exists():
        size_kb = path.stat().st_size // 1024
        print(f"  ✓ {m:<40} ({size_kb} KB)")
    else:
        print(f"  ✗ MISSING: {m}")

# ─────────────────────────────────────────
# Step 2: Check artifact files exist
# ─────────────────────────────────────────
print("\n--- Checking artifact files ---")

expected_artifacts = [
    "X_test_enc.npy",
    "y_test_enc.npy",
    "y_train_balanced.npy",
    "balanced_feature_cols.csv",
    "best_threshold.npy",
]

for a in expected_artifacts:
    path = artifacts_dir / a
    if path.exists():
        print(f"  ✓ {a}")
    else:
        print(f"  ✗ MISSING: {a}")

# ─────────────────────────────────────────
# Step 3: Load test data
# ─────────────────────────────────────────
print("\n--- Loading test data ---")

try:
    X_test = np.load(artifacts_dir / "X_test_enc.npy", allow_pickle=True)
    y_test = np.load(artifacts_dir / "y_test_enc.npy", allow_pickle=True)
    print(f"  ✓ X_test shape  : {X_test.shape}")
    print(f"  ✓ y_test shape  : {y_test.shape}")
    print(f"  ✓ Expired in test : {int(y_test.sum())} / {len(y_test)}")
except Exception as e:
    print(f"  ✗ Failed to load test data: {e}")
    sys.exit(1)

# ─────────────────────────────────────────
# Step 4: Load threshold
# ─────────────────────────────────────────
try:
    threshold = float(np.load(artifacts_dir / "best_threshold.npy")[0])
    print(f"  ✓ Threshold     : {threshold}")
except Exception as e:
    print(f"  ✗ Failed to load threshold: {e}")
    threshold = 0.15
    print(f"  → Using default threshold: {threshold}")

# ─────────────────────────────────────────
# Step 5: Test each model
# ─────────────────────────────────────────
from sklearn.metrics import roc_auc_score, recall_score, f1_score, precision_score

print("\n--- Running predictions on test set ---")
print("-" * 55)
print(f"  Threshold used: {threshold}\n")

model_files = {
    "Random Forest":        "track3_random_forest.pkl",
    "XGBoost":              "track3_xgboost.pkl",
    "Logistic Regression":  "track3_logistic_regression.pkl",
    "Best Model":           "track3_best_model.pkl",
    "XGBoost SMOTE":        "track3_xgboost_smote.pkl",
    "Best Model SMOTE":     "track3_best_model_smote.pkl",
    "RF Calibrated":        "track3_rf_calibrated.pkl",
    "XGB Calibrated":       "track3_xgb_calibrated.pkl",
}

results = []

for name, fname in model_files.items():
    path = models_dir / fname
    if not path.exists():
        print(f"  ✗ {name}: file not found")
        continue
    try:
        model = joblib.load(path)
        proba = model.predict_proba(X_test)[:, 1]
        preds = (proba >= threshold).astype(int)

        auc       = roc_auc_score(y_test, proba)
        recall    = recall_score(y_test, preds, zero_division=0)
        precision = precision_score(y_test, preds, zero_division=0)
        f1        = f1_score(y_test, preds, zero_division=0)
        tp        = int(((preds == 1) & (y_test == 1)).sum())
        fp        = int(((preds == 1) & (y_test == 0)).sum())
        fn        = int(((preds == 0) & (y_test == 1)).sum())
        tn        = int(((preds == 0) & (y_test == 0)).sum())

        print(f"  ✓ {name}")
        print(f"     ROC-AUC  : {auc:.4f}")
        print(f"     Recall   : {recall:.4f}  ({tp}/{tp+fn} expired caught)")
        print(f"     Precision: {precision:.4f}")
        print(f"     F1       : {f1:.4f}")
        print(f"     TP={tp}  FP={fp}  FN={fn}  TN={tn}")
        print()

        results.append({
            "Model":     name,
            "ROC-AUC":   round(auc, 4),
            "Recall":    round(recall, 4),
            "Precision": round(precision, 4),
            "F1":        round(f1, 4),
            "TP": tp, "FP": fp, "FN": fn,
        })

    except Exception as e:
        print(f"  ✗ {name} failed: {e}\n")

# ─────────────────────────────────────────
# Step 6: Summary table
# ─────────────────────────────────────────
print("=" * 55)
print("FINAL MODEL COMPARISON")
print("=" * 55)

if results:
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))

    best_auc    = df_results.loc[df_results["ROC-AUC"].idxmax()]
    best_recall = df_results.loc[df_results["Recall"].idxmax()]

    print(f"\n  Best ROC-AUC : {best_auc['Model']} ({best_auc['ROC-AUC']})")
    print(f"  Best Recall  : {best_recall['Model']} ({best_recall['Recall']})")
else:
    print("  No models were successfully evaluated.")

print("\n" + "=" * 50)
print("MODEL TESTING COMPLETE")
print("=" * 50)