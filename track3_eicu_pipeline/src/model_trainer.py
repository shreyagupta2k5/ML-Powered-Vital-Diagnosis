"""
model_trainer.py
End-to-end train / evaluate / save for the ICU pipeline.
"""
import numpy as np
import pandas as pd
import pathlib
import joblib
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    recall_score, precision_score, f1_score,
    confusion_matrix,
)
from xgboost import XGBClassifier
from imblearn.combine import SMOTETomek
from imblearn.over_sampling import SMOTE


DROP_COLS = [
    "patientunitstayid", "unitdischargeoffset",
    "predictedicumortality", "predictediculos",
    "apachescore", "acutephysiologyscore",
]
TARGET = "mortality_label"


def build_pipeline(X_tr: pd.DataFrame, y_tr: pd.Series) -> Pipeline:
    cat_cols = X_tr.select_dtypes(include="object").columns.tolist()
    num_cols = X_tr.select_dtypes(exclude="object").columns.tolist()

    preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("imp",   SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), num_cols),
        ("cat", Pipeline([
            ("imp", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore")),
        ]), cat_cols),
    ])

    spw = (y_tr == 0).sum() / max((y_tr == 1).sum(), 1)

    pipe = Pipeline([
        ("prep",   preprocessor),
        ("select", SelectKBest(mutual_info_classif, k=100)),
        ("clf",    XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            scale_pos_weight=spw, eval_metric="aucpr",
            random_state=42,
        )),
    ])
    pipe.fit(X_tr, y_tr)
    return pipe


def smote_balance(X_train, y_train, k_neighbors=5):
    smt = SMOTETomek(
        smote=SMOTE(k_neighbors=k_neighbors, random_state=42),
        random_state=42,
    )
    return smt.fit_resample(X_train, y_train)


def evaluate_model(
    model,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float = 0.15,
) -> dict:
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
    metrics = {
        "roc_auc":   round(roc_auc_score(y_test, proba), 4),
        "pr_auc":    round(average_precision_score(y_test, proba), 4),
        "recall":    round(recall_score(y_test, preds, zero_division=0), 4),
        "precision": round(precision_score(y_test, preds, zero_division=0), 4),
        "f1":        round(f1_score(y_test, preds, zero_division=0), 4),
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        "threshold": threshold,
    }
    for k, v in metrics.items():
        print(f"  {k:<12}: {v}")
    return metrics


def find_best_threshold(
    y_true, y_prob, min_precision: float = 0.20
) -> tuple:
    best_t, best_rec = 0.5, -1.0
    for t in np.arange(0.05, 0.90, 0.01):
        preds = (y_prob >= t).astype(int)
        rec   = recall_score(y_true, preds, zero_division=0)
        prec  = precision_score(y_true, preds, zero_division=0)
        if prec >= min_precision and rec > best_rec:
            best_rec, best_t = rec, t
    return round(best_t, 2), round(best_rec, 4)
