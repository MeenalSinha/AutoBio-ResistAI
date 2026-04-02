"""
autobio_engine.py
-----------------
The AutoBio Engine: trains multiple classifiers, evaluates them,
auto-selects the best model, and exposes a unified predict interface.
"""

import time
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, classification_report, confusion_matrix,
)
import xgboost as xgb
import joblib
import os
import optuna
import logging
optuna.logging.set_verbosity(optuna.logging.WARNING)

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

def _build_models() -> Dict[str, Any]:
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            solver="lbfgs",
            C=1.0,
            class_weight="balanced",
            random_state=42,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=1,  # fixed: was -1, OOM in containers
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=1,  # fixed: was -1, OOM in containers
        ),
    }


# ---------------------------------------------------------------------------
# AutoBio Engine
# ---------------------------------------------------------------------------

class AutoBioEngine:
    """
    Self-optimizing ML engine for antibiotic resistance prediction.

    Workflow:
      1. train_all()   — fit every model, capture metrics
      2. select_best() — pick champion by F1 (weighted)
      3. predict()     — use champion for inference
    """

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.results: Dict[str, Dict] = {}
        self.best_model_name: str = ""
        self.best_model: Any = None
        self.feature_names: List[str] = []
        self.class_names: List[str] = []
        self._is_trained: bool = False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train_all(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
        class_names: List[str],
        cv_folds: int = 5,
        optimize_hyperparameters: bool = False,
    ) -> Dict[str, Dict]:
        """
        Train every model in the registry and collect evaluation metrics.
        Returns a dict of model_name -> metrics.
        """
        self.feature_names = feature_names
        self.class_names = class_names
        self.models = _build_models()
        self.results = {}

        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)

        if optimize_hyperparameters:
            self._run_bayesian_optimization(X_train, y_train, cv)

        for name, model in self.models.items():
            t0 = time.time()

            # Cross-validation
            cv_scores = cross_validate(
                model, X_train, y_train,
                cv=cv,
                scoring={
                    "accuracy": "accuracy",
                    "f1_weighted": "f1_weighted",
                    "precision_weighted": "precision_weighted",
                    "recall_weighted": "recall_weighted"
                },
                n_jobs=1,
            )

            # Fit on full training set
            model.fit(X_train, y_train)
            train_time = round(time.time() - t0, 3)

            # Hold-out test evaluation
            y_pred = model.predict(X_test)
            y_proba = (
                model.predict_proba(X_test)
                if hasattr(model, "predict_proba") else None
            )

            cm = confusion_matrix(y_test, y_pred).tolist()
            report = classification_report(
                y_test, y_pred,
                target_names=class_names,
                output_dict=True,
                zero_division=0,
            )

            self.results[name] = {
                "accuracy":          round(accuracy_score(y_test, y_pred), 4),
                "precision":         round(precision_score(y_test, y_pred, average="weighted", zero_division=0), 4),
                "recall":            round(recall_score(y_test, y_pred, average="weighted", zero_division=0), 4),
                "f1_score":          round(f1_score(y_test, y_pred, average="weighted", zero_division=0), 4),
                "cv_accuracy_mean":  round(float(cv_scores["test_accuracy"].mean()), 4),
                "cv_accuracy_std":   round(float(cv_scores["test_accuracy"].std()), 4),
                "cv_f1_mean":        round(float(cv_scores["test_f1_weighted"].mean()), 4),
                "cv_f1_std":         round(float(cv_scores["test_f1_weighted"].std()), 4),
                "cv_precision_mean": round(float(cv_scores["test_precision_weighted"].mean()), 4),
                "cv_recall_mean":    round(float(cv_scores["test_recall_weighted"].mean()), 4),
                "confusion_matrix":  cm,
                "classification_report": report,
                "training_time_s":   train_time,
            }

        self._is_trained = True
        self.select_best()
        return self.results

    def _run_bayesian_optimization(self, X_train: np.ndarray, y_train: np.ndarray, cv: StratifiedKFold):
        """Perform Optuna Bayesian Optimization for XGBoost."""
        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 15),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
                "eval_metric": "mlogloss",
                "random_state": 42,
                "n_jobs": 1,
            }
            model = xgb.XGBClassifier(**params)
            scores = cross_validate(model, X_train, y_train, cv=cv, scoring={"f1_weighted": "f1_weighted"}, n_jobs=1)
            return scores["test_f1_weighted"].mean()

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=10) # 10 trials for speed in production UI, can be increased
        
        # Inject the best model back into the pipeline
        best_xgb = xgb.XGBClassifier(**study.best_params, eval_metric="mlogloss", random_state=42, n_jobs=1)
        self.models["XGBoost (Optuna Optimized)"] = best_xgb

    # ------------------------------------------------------------------
    # Model selection
    # ------------------------------------------------------------------

    def select_best(self) -> str:
        """Select the model with the highest weighted F1 on the hold-out set."""
        best_name = max(self.results, key=lambda n: self.results[n]["f1_score"])
        self.best_model_name = best_name
        self.best_model = self.models[best_name]
        return best_name

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Run inference with the best model.

        Returns:
          prediction      — class label string
          class_index     — integer class index
          confidence      — probability of predicted class
          probabilities   — full class probability vector
        """
        if not self._is_trained:
            raise RuntimeError("Engine has not been trained yet. Call train_all() first.")

        proba = self.best_model.predict_proba(X)[0]
        class_idx = int(np.argmax(proba))
        label = self.class_names[class_idx] if self.class_names else str(class_idx)

        return {
            "prediction":   label,
            "class_index":  class_idx,
            "confidence":   round(float(proba[class_idx]), 4),
            "probabilities": {
                self.class_names[i]: round(float(p), 4)
                for i, p in enumerate(proba)
            },
        }

    # ------------------------------------------------------------------
    # Comparison table
    # ------------------------------------------------------------------

    def get_comparison_table(self) -> List[Dict]:
        """Return a list of per-model metric dicts suitable for JSON serialisation."""
        rows = []
        for name, metrics in self.results.items():
            rows.append({
                "model":          name,
                "accuracy":       metrics["accuracy"],
                "precision":      metrics["precision"],
                "recall":         metrics["recall"],
                "f1_score":       metrics["f1_score"],
                "cv_f1_mean":     metrics["cv_f1_mean"],
                "cv_f1_std":      metrics["cv_f1_std"],
                "training_time_s": metrics["training_time_s"],
                "is_best":        name == self.best_model_name,
            })
        # Sort by F1 descending
        rows.sort(key=lambda r: r["f1_score"], reverse=True)
        return rows

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, directory: str = "models"):
        """Persist the best model and engine state."""
        os.makedirs(directory, exist_ok=True)
        joblib.dump(self.best_model, os.path.join(directory, "best_model.joblib"))
        joblib.dump(self, os.path.join(directory, "engine.joblib"))

    @classmethod
    def load(cls, directory: str = "models") -> "AutoBioEngine":
        """Load a previously saved engine."""
        return joblib.load(os.path.join(directory, "engine.joblib"))

    # ------------------------------------------------------------------
    # Feature importance (tree-based fallback)
    # ------------------------------------------------------------------

    def get_feature_importances(self) -> Optional[Dict[str, float]]:
        """Return feature importances from the best model if available."""
        model = self.best_model
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            return dict(zip(self.feature_names, importances.tolist()))
        if hasattr(model, "coef_"):
            # For Logistic Regression take mean absolute coefficient
            coef = np.abs(model.coef_).mean(axis=0)
            return dict(zip(self.feature_names, coef.tolist()))
        return None
