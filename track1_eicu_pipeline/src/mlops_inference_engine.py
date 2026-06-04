"""
mlops_inference_engine.py
Train, predict, evaluate, and auto-retrain the ICU model.
"""
import joblib
import pathlib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    f1_score, roc_auc_score,
    precision_recall_curve, auc,
)


class MLOpsInferenceEngine:

    def __init__(self, model_path: str = None):
        if model_path and pathlib.Path(model_path).exists():
            self.model = joblib.load(model_path)
        else:
            self.model = RandomForestClassifier(
                n_estimators=200,
                random_state=42,
                class_weight="balanced",
            )

    def train(self, X_train, y_train) -> None:
        print("Training model...")
        self.model.fit(X_train, y_train)
        print("Training complete.")

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X) -> np.ndarray:
        return self.model.predict_proba(X)[:, 1]

    def evaluate(self, X_test, y_test) -> dict:
        preds = self.predict(X_test)
        probs = self.predict_proba(X_test)
        f1        = f1_score(y_test, preds, zero_division=0)
        auc_score = roc_auc_score(y_test, probs)
        prec, rec, _ = precision_recall_curve(y_test, probs)
        pr_auc    = auc(rec, prec)
        print(f"ROC-AUC: {auc_score:.4f} | F1: {f1:.4f} | PR-AUC: {pr_auc:.4f}")
        return {"roc_auc": auc_score, "f1": f1, "pr_auc": pr_auc}

    def auto_retrain(
        self,
        drift_flag: bool,
        X_train,
        y_train,
        save_path: str = "model.joblib",
    ) -> None:
        if drift_flag:
            print("DRIFT DETECTED → retraining model")
            self.train(X_train, y_train)
            joblib.dump(self.model, save_path)
            print(f"Model saved → {save_path}")
        else:
            print("No drift → keeping existing model")
