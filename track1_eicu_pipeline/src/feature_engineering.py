"""
feature_engineering.py
Trend (slope), volatility, and risk-window features.
"""
import pandas as pd
import numpy as np
from functools import reduce


class FeatureEngineeringEngine:
    """
    Builds advanced time-series features per patient:
    slope-based trend, coefficient-of-variation volatility,
    and percentile-based risk window statistics.
    """

    def compute_trend(
        self,
        df: pd.DataFrame,
        group_col: str,
        time_col: str,
        feature: str,
    ) -> pd.DataFrame:
        def slope(x):
            x = x.dropna()
            return np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else np.nan

        out = (
            df.sort_values(time_col)
              .groupby(group_col)[feature]
              .apply(slope)
              .reset_index()
        )
        out.columns = [group_col, f"{feature}_trend"]
        return out

    def compute_volatility(
        self, df: pd.DataFrame, group_col: str, feature: str
    ) -> pd.DataFrame:
        vol = df.groupby(group_col)[feature].agg(["std", "mean"])
        vol[f"{feature}_volatility"] = vol["std"] / (vol["mean"] + 1e-6)
        return vol.reset_index()[[group_col, f"{feature}_volatility"]]

    def compute_risk_window(
        self, df: pd.DataFrame, group_col: str, feature: str
    ) -> pd.DataFrame:
        risk = df.groupby(group_col)[feature].agg(
            min_val="min",
            max_val="max",
            p10=lambda x: np.nanpercentile(x.dropna(), 10) if len(x.dropna()) else np.nan,
            p90=lambda x: np.nanpercentile(x.dropna(), 90) if len(x.dropna()) else np.nan,
        ).rename(columns={
            "min_val": f"{feature}_min",
            "max_val": f"{feature}_max",
            "p10":     f"{feature}_p10",
            "p90":     f"{feature}_p90",
        })
        return risk.reset_index()

    def build(
        self,
        df: pd.DataFrame,
        group_col: str = "patientunitstayid",
        time_col: str = "observationoffset",
    ) -> pd.DataFrame:
        key_features = [
            c for c in ["heartrate", "systemicmean",
                         "respiration", "sao2", "glucose"]
            if c in df.columns
        ]
        feature_sets = []
        for feat in key_features:
            trend = self.compute_trend(df, group_col, time_col, feat)
            vol   = self.compute_volatility(df, group_col, feat)
            risk  = self.compute_risk_window(df, group_col, feat)
            merged = trend.merge(vol,  on=group_col, how="outer")                           .merge(risk, on=group_col, how="outer")
            feature_sets.append(merged)

        return reduce(
            lambda l, r: pd.merge(l, r, on=group_col, how="outer"),
            feature_sets,
        )
