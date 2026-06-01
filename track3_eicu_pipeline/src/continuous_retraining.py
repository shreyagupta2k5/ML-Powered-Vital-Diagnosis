"""
continuous_retraining.py
Automated PSI + KS drift detection → retrain → deploy loop.
"""
import json
import pathlib
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from scipy.stats import ks_2samp

from model_trainer import build_pipeline, evaluate_model


def calculate_psi(
    expected: np.ndarray, actual: np.ndarray, bins: int = 10
) -> float:
    expected = expected[~np.isnan(expected)]
    actual   = actual[~np.isnan(actual)]
    if len(expected) < 10 or len(actual) < 10:
        return 0.0
    bp = np.unique(
        np.percentile(expected, np.linspace(0, 100, bins + 1))
    )
    if len(bp) < 3:
        return 0.0
    exp_c, _ = np.histogram(expected, bins=bp)
    act_c, _ = np.histogram(actual,   bins=bp)
    exp_p = np.where(exp_c == 0, 1e-4, exp_c / (exp_c.sum() + 1e-8))
    act_p = np.where(act_c == 0, 1e-4, act_c / (act_c.sum() + 1e-8))
    return float(np.sum((act_p - exp_p) * np.log(act_p / exp_p)))


def scan_drift(
    baseline_df: pd.DataFrame,
    new_batch_df: pd.DataFrame,
    numeric_features: list,
    psi_threshold: float = 0.25,
    ks_alpha: float = 0.05,
) -> pd.DataFrame:
    rows = []
    for col in numeric_features:
        if col not in baseline_df.columns or col not in new_batch_df.columns:
            continue
        base = baseline_df[col].dropna().values
        curr = new_batch_df[col].dropna().values
        if len(base) < 10 or len(curr) < 10:
            continue
        psi      = calculate_psi(base, curr)
        ks, pval = ks_2samp(base, curr)
        rows.append({
            "feature":        col,
            "psi":            round(psi, 4),
            "ks_stat":        round(ks, 4),
            "p_value":        round(pval, 6),
            "drift_detected": (psi > psi_threshold) or (pval < ks_alpha),
        })
    return pd.DataFrame(rows)


def run_retrain_loop(
    X_pool: pd.DataFrame,
    y_pool: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_path: str,
    log_path: str,
    n_rounds: int = 4,
    batch_fraction: float = 0.2,
    psi_max_threshold: float = 0.50,
    min_drift_features: int = 3,
) -> list:
    """
    Simulate n_rounds of incoming data batches.
    Retrain and redeploy if drift exceeds thresholds.
    Returns the retrain log as a list of dicts.
    """
    from sklearn.metrics import roc_auc_score

    model_path = pathlib.Path(model_path)
    log_path   = pathlib.Path(log_path)

    current_model = joblib.load(model_path) if model_path.exists() else build_pipeline(X_pool, y_pool)
    numeric_cols  = X_pool.select_dtypes(include=np.number).columns[:50].tolist()
    batch_size    = max(50, int(len(X_pool) * batch_fraction))

    log = json.loads(log_path.read_text()) if log_path.exists() else []
    rng = np.random.RandomState(42)

    for round_num in range(1, n_rounds + 1):
        print(f"\n{'─'*55}")
        print(f"ROUND {round_num} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        idx   = rng.choice(len(X_pool), size=batch_size, replace=True)
        X_new = X_pool.iloc[idx].copy().reset_index(drop=True)
        y_new = y_pool.iloc[idx].copy().reset_index(drop=True)

        pre_proba = current_model.predict_proba(X_test)[:, 1]
        pre_auc   = roc_auc_score(y_test, pre_proba)

        drift_df      = scan_drift(X_pool[numeric_cols], X_new[numeric_cols], numeric_cols)
        n_sig         = int((drift_df["psi"] > 0.25).sum())
        max_psi       = float(drift_df["psi"].max())
        top_drifted   = drift_df.nlargest(3, "psi")["feature"].tolist()

        retrain = max_psi > psi_max_threshold or n_sig >= min_drift_features
        action  = "skipped"
        post_auc = None

        if retrain:
            X_pool = pd.concat([X_pool, X_new], ignore_index=True)
            y_pool = pd.concat([y_pool, y_new], ignore_index=True)
            new_model  = build_pipeline(X_pool, y_pool)
            post_proba = new_model.predict_proba(X_test)[:, 1]
            post_auc   = roc_auc_score(y_test, post_proba)
            if post_auc >= pre_auc - 0.01:
                current_model = new_model
                joblib.dump(current_model, model_path)
                action = "deployed"
                print(f"Deployed | post-AUC {post_auc:.4f}")
            else:
                action   = "rejected"
                post_auc = pre_auc
                print(f"Rejected (AUC regression) | kept {pre_auc:.4f}")
        else:
            print(f"No significant drift — skipping")

        entry = {
            "round":            round_num,
            "timestamp":        datetime.now().isoformat()[:16],
            "pre_retrain_auc":  round(pre_auc, 4),
            "post_retrain_auc": round(post_auc, 4) if post_auc else None,
            "action":           action,
            "n_significant":    n_sig,
            "new_batch_size":   len(X_new),
            "max_psi":          round(max_psi, 4),
            "drifted_features": top_drifted,
        }
        log.append(entry)
        log_path.write_text(json.dumps(log, indent=2))

    return log
