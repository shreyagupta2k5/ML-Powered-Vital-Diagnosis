import pandas as pd

targets = {
    "Low SPO2":
        "models/results/low_spo2/model_comparison.csv",

    "Hypotension":
        "models/results/hypotension/model_comparison.csv",

    "Tachycardia":
        "models/results/tachycardia/model_comparison.csv"
}

best_models = []

for target, file in targets.items():

    df = pd.read_csv(file)

    best_row = df.loc[
        df["ROC_AUC"].idxmax()
    ]

    best_models.append([
        target,
        best_row["Model"],
        best_row["Accuracy"],
        best_row["Precision"],
        best_row["Recall"],
        best_row["F1"],
        best_row["ROC_AUC"]
    ])

best_df = pd.DataFrame(
    best_models,
    columns=[
        "Target",
        "Best_Model",
        "Accuracy",
        "Precision",
        "Recall",
        "F1",
        "ROC_AUC"
    ]
)

best_df.to_csv(
    "results/best_models.csv",
    index=False
)

print(best_df)

print("\nSaved Successfully")