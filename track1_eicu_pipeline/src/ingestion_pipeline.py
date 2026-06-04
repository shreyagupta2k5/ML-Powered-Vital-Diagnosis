"""
ingestion_pipeline.py
Schema validation, clinical value cleaning, and imputation.
"""
import pandas as pd
import numpy as np


class IngestionPipeline:
    """
    Validates schema, removes physiologically impossible values,
    and imputes missing data from a reference baseline or medians.
    """

    def __init__(self, reference_stats: dict = None):
        self.reference_stats = reference_stats

    def validate_schema(
        self, df: pd.DataFrame, required_cols: list
    ) -> pd.DataFrame:
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            print(f"WARNING: Missing columns: {missing}")
        return df

    def clean_clinical_values(self, df: pd.DataFrame) -> pd.DataFrame:
        limits = {
            "heartrate": (20, 250),
            "glucose":   (30, 800),
            "sao2":      (40, 100),
        }
        for col, (lo, hi) in limits.items():
            if col in df.columns:
                df.loc[(df[col] < lo) | (df[col] > hi), col] = np.nan
        return df

    def impute_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.select_dtypes(include=[np.number]).columns:
            fill = (
                self.reference_stats[col]["median"]
                if self.reference_stats and col in self.reference_stats
                else df[col].median()
            )
            df[col] = df[col].fillna(fill)
        return df

    def run(
        self,
        df: pd.DataFrame,
        required_cols: list = None,
    ) -> pd.DataFrame:
        if required_cols:
            df = self.validate_schema(df, required_cols)
        df = self.clean_clinical_values(df)
        df = self.impute_missing(df)
        return df
