"""
reference_statistics_store.py
Freeze training-time feature distributions as a baseline
for drift detection.
"""
import json
import pathlib
import numpy as np
import pandas as pd


class ReferenceStatisticsStore:

    def __init__(
        self,
        output_path: str = "reference_statistics.json",
    ):
        """
        output_path: where to save/load the JSON baseline.
        Default is current working directory (works locally + Colab).
        Pass a full path like '/content/eicu_processed/reference_statistics.json'
        when running in Colab.
        """
        self.output_path = pathlib.Path(output_path)
        self.stats: dict = {}

    def build_reference(
        self,
        df: pd.DataFrame,
        group_col: str = "patientunitstayid",
    ) -> dict:
        exclude = {group_col, "mortality_label"}
        cols = [c for c in df.select_dtypes(include=[np.number]).columns
                if c not in exclude]
        for c in cols:
            self.stats[c] = {
                "mean":   float(df[c].mean()),
                "std":    float(df[c].std()),
                "median": float(df[c].median()),
                "min":    float(df[c].min()),
                "max":    float(df[c].max()),
                "q10":    float(df[c].quantile(0.1)),
                "q90":    float(df[c].quantile(0.9)),
            }
        print(f"Captured {len(self.stats)} feature statistics")
        return self.stats

    def save(self) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w") as f:
            json.dump(self.stats, f, indent=4)
        print(f"Saved → {self.output_path}")

    def load(self) -> dict:
        with open(self.output_path) as f:
            self.stats = json.load(f)
        print("Reference statistics loaded")
        return self.stats
