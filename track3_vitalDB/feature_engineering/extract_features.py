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
# WINDOWED DATA DIRECTORY
# =====================================================

WINDOW_DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
    "windowed"
)

# =====================================================
# FEATURE OUTPUT DIRECTORY
# =====================================================

FEATURE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "features"
)

os.makedirs(FEATURE_DIR, exist_ok=True)

# =====================================================
# FINAL FEATURE DATASET
# =====================================================

all_features = []

# =====================================================
# GET CASE FOLDERS
# =====================================================

case_folders = [
    folder for folder in os.listdir(WINDOW_DATA_DIR)
    if os.path.isdir(
        os.path.join(WINDOW_DATA_DIR, folder)
    )
]

print(f"\nTotal Cases: {len(case_folders)}")

# =====================================================
# PROCESS EACH CASE
# =====================================================

for case_folder in case_folders:

    print("\n" + "=" * 60)

    print(f"Processing Case: {case_folder}")

    case_path = os.path.join(
        WINDOW_DATA_DIR,
        case_folder
    )

    window_files = [
        file for file in os.listdir(case_path)
        if file.endswith(".csv")
    ]

    print(f"Total Windows: {len(window_files)}")

    # =================================================
    # PROCESS EACH WINDOW
    # =================================================

    for window_file in window_files:

        try:

            # --------------------------------------------
            # LOAD WINDOW
            # --------------------------------------------

            window_path = os.path.join(
                case_path,
                window_file
            )

            df = pd.read_csv(window_path)

            # --------------------------------------------
            # FEATURE DICTIONARY
            # --------------------------------------------

            features = {}

            # --------------------------------------------
            # IDENTIFIERS
            # --------------------------------------------

            features["case"] = case_folder

            features["window"] = window_file

            # =================================================
            # HR FEATURES
            # =================================================

            features["mean_hr"] = df["HR"].mean()

            features["std_hr"] = df["HR"].std()

            features["min_hr"] = df["HR"].min()

            features["max_hr"] = df["HR"].max()

            # =================================================
            # MAP FEATURES
            # =================================================

            features["mean_map"] = df["MAP"].mean()

            features["std_map"] = df["MAP"].std()

            features["min_map"] = df["MAP"].min()

            features["max_map"] = df["MAP"].max()

            features["map_range"] = (
                df["MAP"].max() - df["MAP"].min()
            )

            # =================================================
            # SPO2 FEATURES
            # =================================================

            features["mean_spo2"] = df["SPO2"].mean()

            features["std_spo2"] = df["SPO2"].std()

            features["min_spo2"] = df["SPO2"].min()

            # =================================================
            # ECG FEATURES
            # =================================================

            features["mean_ecg"] = df["ECG"].mean()

            features["std_ecg"] = df["ECG"].std()

            features["min_ecg"] = df["ECG"].min()

            features["max_ecg"] = df["ECG"].max()

            # =================================================
            # ADD TO FINAL DATASET
            # =================================================

            all_features.append(features)

        except Exception as e:

            print(f"\nError Processing Window: {window_file}")

            print(e)

# =====================================================
# CREATE FINAL FEATURE DATAFRAME
# =====================================================

feature_df = pd.DataFrame(all_features)

# =====================================================
# SAVE FINAL FEATURE DATASET
# =====================================================

save_path = os.path.join(
    FEATURE_DIR,
    "vitaldb_features.csv"
)

feature_df.to_csv(
    save_path,
    index=False
)

print("\nFeature Engineering Completed Successfully.")

print(f"\nFinal Feature Dataset Shape: {feature_df.shape}")

print(f"\nSaved Features To:")

print(save_path)