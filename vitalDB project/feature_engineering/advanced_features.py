import pandas as pd
import numpy as np
import os

# =====================================================
# PROJECT ROOT DIRECTORY
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# =====================================================
# BASIC FEATURE DATASET
# =====================================================

FEATURE_PATH = os.path.join(
    BASE_DIR,
    "data",
    "features",
    "vitaldb_features.csv"
)

# =====================================================
# OUTPUT DIRECTORY
# =====================================================

ADVANCED_FEATURE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "advanced_features"
)

os.makedirs(ADVANCED_FEATURE_DIR, exist_ok=True)

# =====================================================
# LOAD DATASET
# =====================================================

df = pd.read_csv(FEATURE_PATH)

print("\nLoaded Feature Dataset")

print(df.shape)

# =====================================================
# MAP VARIABILITY
# =====================================================

df["map_variability"] = (
    df["std_map"] / df["mean_map"]
)

# =====================================================
# HR VARIABILITY
# =====================================================

df["hr_variability"] = (
    df["std_hr"] / df["mean_hr"]
)

# =====================================================
# ECG RANGE
# =====================================================

df["ecg_range"] = (
    df["max_ecg"] - df["min_ecg"]
)

# =====================================================
# MAP DROP FEATURE
# =====================================================

df["map_drop"] = (
    df["mean_map"] - df["min_map"]
)

# =====================================================
# SPO2 DROP FEATURE
# =====================================================

df["spo2_drop"] = (
    df["mean_spo2"] - df["min_spo2"]
)

# =====================================================
# HYPOTENSION LABEL
# =====================================================

df["hypotension_label"] = np.where(
    df["mean_map"] < 65,
    1,
    0
)

# =====================================================
# TACHYCARDIA LABEL
# =====================================================

df["tachycardia_label"] = np.where(
    df["mean_hr"] > 100,
    1,
    0
)

# =====================================================
# LOW SPO2 LABEL
# =====================================================

df["low_spo2_label"] = np.where(
    df["min_spo2"] < 94,
    1,
    0
)

# =====================================================
# PRINT LABEL COUNTS
# =====================================================

print("\nHypotension Label Distribution:")

print(df["hypotension_label"].value_counts())

print("\nTachycardia Label Distribution:")

print(df["tachycardia_label"].value_counts())

print("\nLow SPO2 Label Distribution:")

print(df["low_spo2_label"].value_counts())

# =====================================================
# FINAL DATASET INFO
# =====================================================

print("\nFinal Dataset Shape:")

print(df.shape)

print("\nMissing Values:")

print(df.isnull().sum())

# =====================================================
# SAVE FINAL DATASET
# =====================================================

save_path = os.path.join(
    ADVANCED_FEATURE_DIR,
    "vitaldb_advanced_features.csv"
)

df.to_csv(
    save_path,
    index=False
)

print("\nAdvanced Feature Dataset Saved Successfully.")

print("\nSaved To:")

print(save_path)