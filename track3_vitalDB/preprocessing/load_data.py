import vitaldb
import pandas as pd
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

os.makedirs(RAW_DATA_DIR, exist_ok=True)

print("\nRaw Data Directory:")

print(RAW_DATA_DIR)

# =====================================================
# REQUIRED TRACKS
# =====================================================

tracks = [
    "SNUADC/ECG_II",          # ECG waveform
    "Solar8000/HR",           # Heart Rate
    "Solar8000/ART_MBP",      # Mean Arterial Pressure
    "Solar8000/PLETH_SPO2"    # Oxygen Saturation
]

# =====================================================
# COLUMN NAMES
# =====================================================

columns = [
    "ECG",
    "HR",
    "MAP",
    "SPO2"
]

# =====================================================
# FIND CASES CONTAINING ALL REQUIRED SIGNALS
# =====================================================

print("\nSearching valid cases...")

cases = vitaldb.find_cases([
    "SNUADC/ECG_II",
    "Solar8000/HR",
    "Solar8000/ART_MBP",
    "Solar8000/PLETH_SPO2"
])

print(f"\nTotal matching cases found: {len(cases)}")

# =====================================================
# NUMBER OF CASES TO LOAD
# =====================================================

NUM_CASES = 100

selected_cases = cases[:NUM_CASES]

print(f"\nDownloading first {NUM_CASES} cases...\n")

# =====================================================
# LOAD EACH CASE
# =====================================================

for caseid in selected_cases:

    print("=" * 60)

    print(f"Loading Case ID: {caseid}")

    try:

        # ------------------------------------------------
        # LOAD SIGNALS
        # ------------------------------------------------

        arr = vitaldb.load_case(
            caseid,
            tracks
        )

        # ------------------------------------------------
        # CHECK EMPTY DATA
        # ------------------------------------------------

        if arr is None:

            print(f"Skipping Case {caseid} -> Empty data")

            continue

        # ------------------------------------------------
        # CHECK VALID DIMENSIONS
        # ------------------------------------------------

        if len(arr.shape) != 2:

            print(f"Skipping Case {caseid} -> Invalid dimensions")

            continue

        # ------------------------------------------------
        # CHECK TRACK COMPLETENESS
        # ------------------------------------------------

        if arr.shape[1] != len(columns):

            print(f"Skipping Case {caseid} -> Missing tracks")

            continue

        # ------------------------------------------------
        # CONVERT TO DATAFRAME
        # ------------------------------------------------

        df = pd.DataFrame(
            arr,
            columns=columns
        )

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
        # REMOVE VERY SHORT RECORDINGS
        # ------------------------------------------------

        if len(df) < 1000:

            print(f"Skipping Case {caseid} -> Recording too short")

            continue

        # ------------------------------------------------
        # PRINT BASIC INFO
        # ------------------------------------------------

        print(f"\nShape: {df.shape}")

        print("\nMissing Values:")

        print(df.isnull().sum())

        print("\nAvailable Non-Null Values:")

        print(df.notnull().sum())

        print("\nSignal Statistics:")

        print(df.describe())

        # ------------------------------------------------
        # SAVE CSV
        # ------------------------------------------------

        save_path = os.path.join(
            RAW_DATA_DIR,
            f"case_{caseid}.csv"
        )

        df.to_csv(
            save_path,
            index=False
        )

        print(f"\nSaved Successfully:")

        print(save_path)

    except Exception as e:

        print(f"\nError in Case {caseid}")

        print(e)

print("\nAll selected cases processed.")