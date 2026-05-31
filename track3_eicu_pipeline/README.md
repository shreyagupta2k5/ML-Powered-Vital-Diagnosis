# Track 3 — eICU ICU Mortality Prediction

## Quick Load (for backend team)
```python
import joblib, json, pandas as pd, numpy as np

manifest     = json.load(open('metadata/model_manifest.json'))
thresholds   = json.load(open('metadata/thresholds.json'))
feature_cols = pd.read_csv('metadata/feature_columns.csv').iloc[:,0].tolist()

# Primary models
best_model   = joblib.load('models/track3_best_model.pkl')         # Random Forest
rf_cal       = joblib.load('models/track3_rf_calibrated.pkl')      # Calibrated RF
xgb_cal      = joblib.load('models/track3_xgb_calibrated.pkl')     # Calibrated XGB
full_pipeline= joblib.load('models/track3_full_pipeline.joblib')   # End-to-end pipeline

# Predict
X_test = pd.DataFrame(np.load('artifacts/X_test_enc.npy'), columns=feature_cols)
probs  = best_model.predict_proba(X_test)[:, 1]
```

## Models
| File | Type | ROC-AUC | Notes |
|---|---|---|---|
| track3_best_model.pkl | Random Forest | 0.8076 | Best recall (0.75 at t=0.15) |
| track3_rf_calibrated.pkl | Calibrated RF | 0.8076 | Use for ensemble |
| track3_xgb_calibrated.pkl | Calibrated XGB | 0.7834 | Use for ensemble |
| track3_xgboost_smote.pkl | XGBoost | 0.7607 | SMOTE-trained |
| track3_full_pipeline.joblib | XGB Pipeline | 0.7530 | Self-contained, no preprocessing needed |
| track3_lstm_bidirectional.keras | BiLSTM | — | 13 features × 24h sequences |

## Thresholds
| Threshold | Recall | FP | Clinical Use |
|---|---|---|---|
| 0.10 | 88% | 164 | Safety-first, catch every death |
| 0.15 | 75% | 95 | **Recommended** |
| 0.30 | 50% | 23 | Balanced alert load |
| 0.35 | 44% | 11 | Best F1 (0.364) |

## Input Features
- 561 features total (from 24h observation window)
- Exact column order: `metadata/feature_columns.csv`
- LSTM input: shape (N, 24, 13) — use `artifacts/X_seq.npy` as reference

## Dataset
- eICU Demo v2.0.1 | 1623 patients | 78 expired (4.81%)
- SMOTE-balanced training: 1231 alive | 1231 expired
- Clean test set: 309 alive | 16 expired

## Key Results Files
- `final_results/smote_model_comparison.csv` — all model metrics
- `final_results/shap_feature_importance.csv` — SHAP feature rankings
- `final_results/threshold_analysis.csv` — full threshold sweep
- `final_results/clinical_decision_summary.csv` — clinical cost analysis
- `final_results/bootstrap_ci.csv` — 95% confidence intervals
- `final_results/loho_validation.csv` — leave-one-hospital-out results
