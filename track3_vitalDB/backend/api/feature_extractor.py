import numpy as np
import pandas as pd

WINDOW_SIZE = 3000
STEP_SIZE = 1000

FEATURE_COLUMNS = [
    "mean_hr",
    "std_hr",
    "min_hr",
    "max_hr",
    "mean_map",
    "std_map",
    "min_map",
    "max_map",
    "map_range",
    "mean_spo2",
    "std_spo2",
    "min_spo2",
    "mean_ecg",
    "std_ecg",
    "min_ecg",
    "max_ecg",
    "map_variability",
    "hr_variability",
    "ecg_range",
    "map_drop",
    "spo2_drop"
]


def segment_signals(ecg, hr, map_signal, spo2):

    windows = []

    signal_length = len(ecg)

    for start in range(
        0,
        signal_length - WINDOW_SIZE + 1,
        STEP_SIZE
    ):

        end = start + WINDOW_SIZE

        windows.append({

            "ecg": ecg[start:end],

            "hr": hr[start:end],

            "map": map_signal[start:end],

            "spo2": spo2[start:end]
        })

    return windows


def extract_features(window):

    ecg = np.array(window["ecg"])
    hr = np.array(window["hr"])
    map_signal = np.array(window["map"])
    spo2 = np.array(window["spo2"])

    features = {

        "mean_hr": np.mean(hr),
        "std_hr": np.std(hr),
        "min_hr": np.min(hr),
        "max_hr": np.max(hr),

        "mean_map": np.mean(map_signal),
        "std_map": np.std(map_signal),
        "min_map": np.min(map_signal),
        "max_map": np.max(map_signal),

        "map_range":
            np.max(map_signal) - np.min(map_signal),

        "mean_spo2": np.mean(spo2),
        "std_spo2": np.std(spo2),
        "min_spo2": np.min(spo2),

        "mean_ecg": np.mean(ecg),
        "std_ecg": np.std(ecg),
        "min_ecg": np.min(ecg),
        "max_ecg": np.max(ecg),

        "map_variability":
            np.std(map_signal),

        "hr_variability":
            np.std(hr),

        "ecg_range":
            np.max(ecg) - np.min(ecg),

        "map_drop":
            np.max(map_signal) - np.min(map_signal),

        "spo2_drop":
            np.max(spo2) - np.min(spo2)
    }

    return pd.DataFrame(
        [features]
    )[FEATURE_COLUMNS]