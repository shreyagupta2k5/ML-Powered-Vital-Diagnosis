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
# RAW DATA DIRECTORY
# =====================================================

RAW_DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw"
)

# =====================================================
# PROCESSED DATA DIRECTORY
# =====================================================

PROCESSED_DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# =====================================================
# REMOVE OLD PROCESSED FILES
# =====================================================

old_files = [
    file for file in os.listdir(PROCESSED_DATA_DIR)
    if file.endswith(".csv")
]

for old_file in old_files:

    old_path = os.path.join(
        PROCESSED_DATA_DIR,
        old_file
    )

    os.remove(old_path)

print("\nOld processed files removed.")

# =====================================================
# GET ONLY CSV FILES
# =====================================================

files = [
    file for file in os.listdir(RAW_DATA_DIR)
    if file.endswith(".csv")
]

print(f"\nTotal raw CSV files found: {len(files)}")

# =====================================================
# PROCESS EACH FILE
# =====================================================

for file in files:

    print("\n" + "=" * 60)

    print(f"Processing File: {file}")

    try:

        # ------------------------------------------------
        # LOAD CSV
        # ------------------------------------------------

        file_path = os.path.join(
            RAW_DATA_DIR,
            file
        )

        df = pd.read_csv(file_path)

        print(f"\nOriginal Shape: {df.shape}")

        # ------------------------------------------------
        # SKIP IF MAP COLUMN COMPLETELY EMPTY
        # ------------------------------------------------

        if df["MAP"].isnull().all():

            print(f"\nSkipping {file} -> MAP completely empty")

            continue

        # ------------------------------------------------
        # REMOVE FULLY EMPTY ROWS
        # ------------------------------------------------

        df.dropna(
            how="all",
            inplace=True
        )

        # ------------------------------------------------
        # RESET INDEX
        # ------------------------------------------------

        df.reset_index(
            drop=True,
            inplace=True
        )

        # ------------------------------------------------
        # REMOVE IMPOSSIBLE HR VALUES
        # ------------------------------------------------

        df.loc[
            (df["HR"] < 20) |
            (df["HR"] > 250),
            "HR"
        ] = np.nan

        # ------------------------------------------------
        # REMOVE IMPOSSIBLE MAP VALUES
        # ------------------------------------------------

        df.loc[
            (df["MAP"] < 40) |
            (df["MAP"] > 200),
            "MAP"
        ] = np.nan

        # ------------------------------------------------
        # REMOVE IMPOSSIBLE SPO2 VALUES
        # ------------------------------------------------

        df.loc[
            (df["SPO2"] < 50) |
            (df["SPO2"] > 100),
            "SPO2"
        ] = np.nan

        # ------------------------------------------------
        # PRINT MISSING VALUES BEFORE CLEANING
        # ------------------------------------------------

        print("\nMissing Values Before Cleaning:")

        print(df.isnull().sum())

        # ------------------------------------------------
        # INTERPOLATION
        # ------------------------------------------------

        df.interpolate(
            method="linear",
            inplace=True
        )

        # ------------------------------------------------
        # BACKWARD FILL
        # ------------------------------------------------

        df.bfill(inplace=True)

        # ------------------------------------------------
        # FORWARD FILL
        # ------------------------------------------------

        df.ffill(inplace=True)

        # ------------------------------------------------
        # REMOVE FULLY EMPTY ROWS AGAIN
        # ------------------------------------------------

        df.dropna(
            how="all",
            inplace=True
        )

        # ------------------------------------------------
        # RESET INDEX AGAIN
        # ------------------------------------------------

        df.reset_index(
            drop=True,
            inplace=True
        )

        # ------------------------------------------------
        # FINAL MAP VALIDATION
        # ------------------------------------------------

        if df["MAP"].isnull().all():

            print(f"\nSkipping {file} -> MAP still empty after cleaning")

            continue

        # ------------------------------------------------
        # REMOVE VERY SHORT RECORDINGS
        # ------------------------------------------------

        if len(df) < 1000:

            print(f"\nSkipping {file} -> Too short after cleaning")

            continue

        # ------------------------------------------------
        # PRINT FINAL INFORMATION
        # ------------------------------------------------

        print(f"\nCleaned Shape: {df.shape}")

        print("\nMissing Values After Cleaning:")

        print(df.isnull().sum())

        print("\nAvailable Non-Null Values:")

        print(df.notnull().sum())

        print("\nSignal Statistics:")

        print(df.describe())

        # ------------------------------------------------
        # SAVE CLEANED FILE
        # ------------------------------------------------

        save_path = os.path.join(
            PROCESSED_DATA_DIR,
            file
        )

        df.to_csv(
            save_path,
            index=False
        )

        print(f"\nSaved Cleaned File:")

        print(save_path)

    except Exception as e:

        print(f"\nError Processing File: {file}")

        print(e)

print("\nAll files cleaned successfully.")