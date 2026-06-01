"""
feature_aggregator.py
Aggregate vitals and labs into per-patient features.
"""
import pandas as pd
import numpy as np
from functools import reduce


def aggregate_features(
    df: pd.DataFrame,
    group_col: str,
    feature_cols: list,
) -> pd.DataFrame:
    """
    Compute mean, min, max, std, count, and coefficient of
    variation for each feature column, grouped by patient.
    """
    agg_dict = {c: ["mean", "min", "max", "std", "count"]
                for c in feature_cols}
    agg = df.groupby(group_col).agg(agg_dict)
    agg.columns = [f"{c}_{s}" for c, s in agg.columns]
    agg = agg.reset_index()

    for c in feature_cols:
        m, s = f"{c}_mean", f"{c}_std"
        if m in agg.columns and s in agg.columns:
            agg[f"{c}_cv"] = agg[s] / (agg[m] + 1e-6)

    return agg


def create_temporal_dataset(
    patient: pd.DataFrame,
    vitalPeriodic: pd.DataFrame,
    vitalAperiodic: pd.DataFrame,
    lab: pd.DataFrame,
    apache: pd.DataFrame,
    window_hours: int,
    processed_dir: str = "/content/eicu_processed",
) -> pd.DataFrame:
    """
    Build a flat ML-ready feature table for a given
    observation window (6, 12, or 24 hours).
    """
    import pathlib
    processed_dir = pathlib.Path(processed_dir)
    processed_dir.mkdir(exist_ok=True)

    window = window_hours * 60
    cohort_ids = patient["patientunitstayid"].unique()

    periodic = vitalPeriodic[
        vitalPeriodic["patientunitstayid"].isin(cohort_ids)
        & vitalPeriodic["observationoffset"].between(0, window)
    ].copy()

    aperiodic = vitalAperiodic[
        vitalAperiodic["patientunitstayid"].isin(cohort_ids)
        & vitalAperiodic["observationoffset"].between(0, window)
    ].copy()

    labs = lab[
        lab["patientunitstayid"].isin(cohort_ids)
        & lab["labresultoffset"].between(0, window)
    ].copy()

    periodic_features = [
        c for c in ["heartrate", "respiration", "sao2",
                    "temperature", "systemicsystolic",
                    "systemicdiastolic", "systemicmean"]
        if c in periodic.columns
    ]
    aperiodic_features = [
        c for c in ["noninvasivesystolic", "noninvasivediastolic",
                    "noninvasivemean"]
        if c in aperiodic.columns
    ]

    periodic_agg  = aggregate_features(periodic,  "patientunitstayid", periodic_features)
    aperiodic_agg = aggregate_features(aperiodic, "patientunitstayid", aperiodic_features)

    labs["labresult"] = pd.to_numeric(labs["labresult"], errors="coerce")
    labs_pivot = labs.pivot_table(
        index="patientunitstayid", columns="labname",
        values="labresult", aggfunc=["mean", "min", "max", "std"]
    )
    labs_pivot.columns = [f"{lab}_{stat}"
                          for stat, lab in labs_pivot.columns]
    labs_pivot = labs_pivot.reset_index()

    ml_df = patient[[
        "patientunitstayid", "gender", "age", "ethnicity",
        "admissionweight", "unitdischargeoffset", "mortality_label"
    ]].copy()

    ml_df = ml_df.merge(periodic_agg,  on="patientunitstayid", how="left")
    ml_df = ml_df.merge(aperiodic_agg, on="patientunitstayid", how="left")
    ml_df = ml_df.merge(labs_pivot,    on="patientunitstayid", how="left")

    apache_keep = [
        "patientunitstayid", "acutephysiologyscore",
        "apachescore", "predictedicumortality", "predictediculos"
    ]
    apache_sub = apache[apache_keep].drop_duplicates(
        subset=["patientunitstayid"]
    )
    ml_df = ml_df.merge(apache_sub, on="patientunitstayid", how="left")

    for c in ml_df.select_dtypes(include=[np.number]).columns:
        ml_df[c] = ml_df[c].fillna(ml_df[c].median())
    for c in ml_df.select_dtypes(include="object").columns:
        ml_df[c] = ml_df[c].fillna(ml_df[c].mode()[0])

    out = processed_dir / f"eicu_ml_features_{window_hours}h.csv.gz"
    ml_df.to_csv(out, compression="gzip", index=False)
    print(f"Saved {window_hours}h dataset → {out}  shape={ml_df.shape}")
    return ml_df
