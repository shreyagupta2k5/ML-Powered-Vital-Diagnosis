import pandas as pd
import numpy as np

class IngestionPipeline:
    def __init__(self, reference_stats=None):
        self.reference_stats = reference_stats

    def validate_schema(self, df, required_cols):
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            print(f"Missing columns: {missing}")
        return df

    def clean_clinical_values(self, df):
        if "heartrate" in df.columns:
            df.loc[(df["heartrate"] < 20) | (df["heartrate"] > 250), "heartrate"] = np.nan
        if "glucose" in df.columns:
            df.loc[(df["glucose"] < 30) | (df["glucose"] > 800), "glucose"] = np.nan
        if "sao2" in df.columns:
            df.loc[(df["sao2"] < 40) | (df["sao2"] > 100), "sao2"] = np.nan
        return df

    def impute_missing(self, df):
        if self.reference_stats is None:
            return df.fillna(df.median(numeric_only=True))
        for col in df.select_dtypes(include=[np.number]).columns:
            if col in self.reference_stats:
                df[col] = df[col].fillna(self.reference_stats[col]["median"])
            else:
                df[col] = df[col].fillna(df[col].median())
        return df

    def run(self, df, required_cols=None):
        if required_cols:
            df = self.validate_schema(df, required_cols)
        df = self.clean_clinical_values(df)
        df = self.impute_missing(df)
        return df
