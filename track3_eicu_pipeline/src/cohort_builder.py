"""
cohort_builder.py
Build ICU cohort from eICU patient table.
"""
import pandas as pd
import numpy as np


def build_cohort(patient_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter adult ICU patients with LOS >= 24h and valid outcomes.
    Returns cohort with mortality_label column added.
    """
    df = patient_df.copy()
    df["age"] = df["age"].replace("> 89", "90")
    df["age"] = pd.to_numeric(df["age"], errors="coerce")

    df = df[df["age"] >= 18]
    df = df[df["unitdischargeoffset"] >= 1440]
    df = df[df["unitdischargestatus"].isin(["Alive", "Expired"])]
    df = df.drop_duplicates(subset=["patientunitstayid"])

    df["mortality_label"] = np.where(
        df["unitdischargestatus"] == "Expired", 1, 0
    )

    print(f"Cohort size   : {len(df)}")
    print(f"Expired       : {df['mortality_label'].sum()}")
    print(f"Alive         : {(df['mortality_label'] == 0).sum()}")
    print(f"Mortality rate: {df['mortality_label'].mean()*100:.2f}%")
    return df
