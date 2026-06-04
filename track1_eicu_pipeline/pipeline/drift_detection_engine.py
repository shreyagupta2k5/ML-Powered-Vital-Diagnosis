import numpy as np
import pandas as pd
import json
from scipy.stats import ks_2samp
import pathlib

class DriftDetectionEngine:
    def __init__(self, reference_path):
        self.reference_path = pathlib.Path(reference_path)
        self.reference_stats = self._load()

    def _load(self):
        with open(self.reference_path) as f:
            return json.load(f)

    def calculate_psi(self, baseline, current, bins=10):
        baseline = np.array(baseline)[~np.isnan(baseline)]
        current  = np.array(current)[~np.isnan(current)]
        if len(baseline) < 10 or len(current) < 10:
            return 0.0
        bp = np.unique(np.percentile(baseline, np.linspace(0, 100, bins + 1)))
        if len(bp) < 3:
            return 0.0
        exp_c, _ = np.histogram(baseline, bins=bp)
        act_c, _ = np.histogram(current,  bins=bp)
        exp_p = np.where(exp_c == 0, 1e-4, exp_c / (exp_c.sum() + 1e-8))
        act_p = np.where(act_c == 0, 1e-4, act_c / (act_c.sum() + 1e-8))
        return float(np.sum((act_p - exp_p) * np.log(act_p / exp_p)))

    def ks_test(self, baseline, current):
        return ks_2samp(baseline, current)

    def scan_drift(self, baseline_df, current_df, psi_thresh=0.25, ks_alpha=0.05):
        results = []
        for feat in self.reference_stats:
            if feat not in current_df.columns:
                continue
            base = baseline_df[feat].dropna().values
            curr = current_df[feat].dropna().values
            if len(base) < 10 or len(curr) < 10:
                continue
            psi = self.calculate_psi(base, curr)
            ks_stat, p_val = self.ks_test(base, curr)
            results.append({
                "feature": feat,
                "psi": round(psi, 4),
                "ks_stat": round(ks_stat, 4),
                "p_value": round(p_val, 6),
                "drift_detected": (psi > psi_thresh) or (p_val < ks_alpha)
            })
        return pd.DataFrame(results)
