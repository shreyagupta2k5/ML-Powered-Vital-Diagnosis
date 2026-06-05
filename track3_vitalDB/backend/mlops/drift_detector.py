import pandas as pd
from scipy.stats import ks_2samp


def detect_drift(
    reference_df,
    incoming_df
):

    results = {}

    for column in incoming_df.columns:

        if column not in reference_df.columns:
            continue

        stat, pvalue = ks_2samp(
            reference_df[column],
            incoming_df[column]
        )

        results[column] = {

            "pvalue":
                float(pvalue),

            "drift":
                bool(pvalue < 0.05)
        }

    return results