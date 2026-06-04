import numpy as np
import pandas as pd
import joblib
import pathlib
from sklearn.metrics import roc_auc_score

class MLOpsInferenceEngine:
    def __init__(self, model_path=None):
        self.model = joblib.load(model_path) if model_path and pathlib.Path(model_path).exists() else None

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)[:, 1]

    def evaluate(self, X_test, y_test):
        probs = self.predict_proba(X_test)
        auc = roc_auc_score(y_test, probs)
        print(f"ROC-AUC: {auc:.4f}")
        return {"roc_auc": auc}
