"""
drift_detection_engine.py
PSI + KS-test drift detection with retrain signal.
"""
import json
import pathlib
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


class DriftDetectionEngine:

    def __init__(self, reference_path: str):
        self.reference_path = pathlib.Path(reference_path)
        self.reference_stats = self._load()

    def _load(self) -> dict:
        with open(self.reference_path) as f:
            return json.load(f)

    def calculate_psi(
        self,
        baseline: np.ndarray,
        current: np.ndarray,
        bins: int = 10,
    ) -> float:
        baseline = baseline[~np.isnan(baseline)]
        current  = current[~np.isnan(current)]
        if len(baseline) < 10 or len(current) < 10:
            return 0.0
        bp = np.unique(
            np.percentile(baseline, np.linspace(0, 100, bins + 1))
        )
        if len(bp) < 3:
            return 0.0
        exp_c, _ = np.histogram(baseline, bins=bp)
        act_c, _ = np.histogram(current,  bins=bp)
        exp_p = np.where(exp_c == 0, 1e-4, exp_c / (exp_c.sum() + 1e-8))
        act_p = np.where(act_c == 0, 1e-4, act_c / (act_c.sum() + 1e-8))
        return float(np.sum((act_p - exp_p) * np.log(act_p / exp_p)))

    def ks_test(
        self, baseline: np.ndarray, current: np.ndarray
    ) -> tuple:
        return ks_2samp(baseline, current)

    def scan_drift(
        self,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        psi_threshold: float = 0.25,
        ks_alpha: float = 0.05,
    ) -> tuple:
        """
        Returns (results_df, alert_flag).
        alert_flag is True when any feature exceeds thresholds.
        """
        rows = []
        alert = False
        for feat in self.reference_stats:
            if feat not in current_df.columns:
                continue
            base = baseline_df[feat].dropna().values
            curr = current_df[feat].dropna().values
            if len(base) < 10 or len(curr) < 10:
                continue
            psi      = self.calculate_psi(base, curr)
            ks, pval = self.ks_test(base, curr)
            drift    = (psi > psi_threshold) or (pval < ks_alpha)
            if drift:
                alert = True
            rows.append({
                "feature":        feat,
                "psi":            round(psi, 4),
                "ks_stat":        round(ks, 4),
                "p_value":        round(pval, 6),
                "drift_detected": drift,
            })
        return pd.DataFrame(rows), alert
