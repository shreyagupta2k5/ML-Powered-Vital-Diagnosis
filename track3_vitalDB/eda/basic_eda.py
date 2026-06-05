import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
# PROCESSED DATA DIRECTORY
# =====================================================

PROCESSED_DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)

# =====================================================
# RESULTS DIRECTORY
# =====================================================

RESULTS_DIR = os.path.join(
    BASE_DIR,
    "results"
)

# =====================================================
# EDA RESULTS DIRECTORY
# =====================================================

EDA_RESULTS_DIR = os.path.join(
    RESULTS_DIR,
    "eda"
)

os.makedirs(EDA_RESULTS_DIR, exist_ok=True)

# =====================================================
# GET ONLY CSV FILES
# =====================================================

files = [
    file for file in os.listdir(PROCESSED_DATA_DIR)
    if file.endswith(".csv")
]

print(f"\nTotal Processed Files: {len(files)}")

# =====================================================
# PROCESS EACH FILE
# =====================================================

for file in files:

    print("\n" + "=" * 60)

    print(f"Running EDA for: {file}")

    try:

        # ------------------------------------------------
        # LOAD FILE
        # ------------------------------------------------

        file_path = os.path.join(
            PROCESSED_DATA_DIR,
            file
        )

        df = pd.read_csv(file_path)

        # ------------------------------------------------
        # CASE NAME
        # ------------------------------------------------

        case_name = file.replace(".csv", "")

        # ------------------------------------------------
        # CREATE CASE-SPECIFIC EDA FOLDER
        # ------------------------------------------------

        case_eda_dir = os.path.join(
            EDA_RESULTS_DIR,
            case_name
        )

        os.makedirs(case_eda_dir, exist_ok=True)

        print(f"\nCreated Folder: {case_eda_dir}")

        # =================================================
        # SAVE STATISTICAL SUMMARY
        # =================================================

        summary_path = os.path.join(
            case_eda_dir,
            "statistical_summary.csv"
        )

        df.describe().to_csv(summary_path)

        # =================================================
        # SAVE MISSING VALUE REPORT
        # =================================================

        missing_values = df.isnull().sum()

        missing_path = os.path.join(
            case_eda_dir,
            "missing_values.csv"
        )

        missing_values.to_csv(missing_path)

        # =================================================
        # ECG WAVEFORM PLOT
        # =================================================

        plt.figure(figsize=(15, 4))

        plt.plot(df["ECG"][:3000])

        plt.title(f"{case_name} - ECG Waveform")

        plt.xlabel("Time")

        plt.ylabel("ECG")

        plt.grid(True)

        ecg_path = os.path.join(
            case_eda_dir,
            "ecg_waveform.png"
        )

        plt.savefig(ecg_path)

        plt.close()

        # =================================================
        # HEART RATE PLOT
        # =================================================

        plt.figure(figsize=(15, 4))

        plt.plot(df["HR"][:5000])

        plt.title(f"{case_name} - Heart Rate")

        plt.xlabel("Time")

        plt.ylabel("HR")

        plt.grid(True)

        hr_path = os.path.join(
            case_eda_dir,
            "heart_rate.png"
        )

        plt.savefig(hr_path)

        plt.close()

        # =================================================
        # MAP PLOT
        # =================================================

        plt.figure(figsize=(15, 4))

        plt.plot(df["MAP"][:5000])

        plt.title(f"{case_name} - Mean Arterial Pressure")

        plt.xlabel("Time")

        plt.ylabel("MAP")

        plt.grid(True)

        map_path = os.path.join(
            case_eda_dir,
            "map_signal.png"
        )

        plt.savefig(map_path)

        plt.close()

        # =================================================
        # SPO2 PLOT
        # =================================================

        plt.figure(figsize=(15, 4))

        plt.plot(df["SPO2"][:5000])

        plt.title(f"{case_name} - SPO2")

        plt.xlabel("Time")

        plt.ylabel("SPO2")

        plt.grid(True)

        spo2_path = os.path.join(
            case_eda_dir,
            "spo2_signal.png"
        )

        plt.savefig(spo2_path)

        plt.close()

        # =================================================
        # HISTOGRAMS
        # =================================================

        histogram_dir = os.path.join(
            case_eda_dir,
            "histograms"
        )

        os.makedirs(histogram_dir, exist_ok=True)

        for column in df.columns:

            plt.figure(figsize=(6, 4))

            sns.histplot(
                df[column],
                kde=True
            )

            plt.title(f"{case_name} - {column} Distribution")

            plt.xlabel(column)

            plt.ylabel("Frequency")

            histogram_path = os.path.join(
                histogram_dir,
                f"{column}_histogram.png"
            )

            plt.savefig(histogram_path)

            plt.close()

        # =================================================
        # CORRELATION HEATMAP
        # =================================================

        plt.figure(figsize=(8, 6))

        sns.heatmap(
            df.corr(),
            annot=True,
            cmap="coolwarm"
        )

        plt.title(f"{case_name} - Correlation Heatmap")

        heatmap_path = os.path.join(
            case_eda_dir,
            "correlation_heatmap.png"
        )

        plt.savefig(heatmap_path)

        plt.close()

        print(f"\nEDA Saved Successfully for {case_name}")

    except Exception as e:

        print(f"\nError Processing {file}")

        print(e)

print("\nAll EDA Results Saved Successfully.")