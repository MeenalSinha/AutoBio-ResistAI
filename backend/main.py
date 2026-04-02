"""
main.py
-------
FastAPI application for AutoBio-ResistAI.
Exposes endpoints for dataset upload, model training, prediction,
explainability, and treatment recommendations.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from data_processor import DataProcessor
from autobio_engine import AutoBioEngine
from explainability import ExplainabilityModule
from treatment import recommend_treatment

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AutoBio-ResistAI API",
    description="Self-optimizing antibiotic resistance prediction system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Singleton state (in-memory session)
# ---------------------------------------------------------------------------

class AppState:
    processor: Optional[DataProcessor] = None
    engine: Optional[AutoBioEngine] = None
    explainer: Optional[ExplainabilityModule] = None
    preprocessed: Optional[Dict[str, Any]] = None
    is_trained: bool = False

state = AppState()

def save_state():
    os.makedirs("models", exist_ok=True)
    joblib.dump({
        "processor": state.processor,
        "engine": state.engine,
        "explainer": state.explainer,
        "preprocessed": state.preprocessed,
        "is_trained": state.is_trained
    }, "models/app_state.joblib")

def load_state():
    if os.path.exists("models/app_state.joblib"):
        saved_state = joblib.load("models/app_state.joblib")
        state.processor = saved_state["processor"]
        state.engine = saved_state["engine"]
        state.explainer = saved_state["explainer"]
        state.preprocessed = saved_state["preprocessed"]
        state.is_trained = saved_state["is_trained"]

# Attempt to load state on startup
load_state()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class PredictRequest(BaseModel):
    features: Dict[str, Any]
    species: Optional[str] = None

class TrainRequest(BaseModel):
    target_column: Optional[str] = ""
    test_size: float = 0.2
    cv_folds: int = 5
    use_sample_data: bool = False
    optimize_hyperparameters: bool = True

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _numpy_safe(obj):
    """Recursively convert numpy types to Python natives for JSON."""
    if isinstance(obj, dict):
        return {k: _numpy_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_numpy_safe(i) for i in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "AutoBio-ResistAI API is running", "status": "ok"}

@app.get("/health")
def health():
    return {
        "status":     "ok",
        "is_trained": state.is_trained,
        "model":      state.engine.best_model_name if state.engine and state.is_trained else None,
    }


# ------------------------------------------------------------------
# 1. Upload dataset
# ------------------------------------------------------------------

@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Accept a CSV or Excel file and return a preview + column info."""
    contents = await file.read()
    proc = DataProcessor()
    try:
        df = proc.load_from_bytes(contents, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Store in session state
    state.processor = proc
    state.processor._uploaded_bytes = contents
    state.processor._uploaded_filename = file.filename

    preview = df.head(5).to_dict(orient="records")
    column_info = [
        {"name": col, "dtype": str(df[col].dtype), "nulls": int(df[col].isnull().sum())}
        for col in df.columns
    ]

    return {
        "filename":    file.filename,
        "rows":        len(df),
        "columns":     len(df.columns),
        "column_info": column_info,
        "preview":     _numpy_safe(preview),
    }


# ------------------------------------------------------------------
# 2. Train models
# ------------------------------------------------------------------

@app.post("/train")
def train_models(request: TrainRequest):
    """
    Run the AutoBio Engine:
      - Preprocess data
      - Train all models
      - Select best
      - Fit SHAP explainer
    """
    proc = state.processor or DataProcessor()

    if request.use_sample_data or state.processor is None:
        # Load from real built-in sample dataset instead of fake synthetic logic
        sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample", "sample_amr_dataset.csv")
        try:
            df = proc.load_from_path(sample_path)
            state.processor = proc
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load sample data: {e}")
    else:
        # Re-load from previously uploaded bytes
        df = proc.load_from_bytes(
            proc._uploaded_bytes,
            proc._uploaded_filename,
        )

    try:
        preprocessed = proc.preprocess(
            df,
            target_column=request.target_column or "",
            test_size=request.test_size,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preprocessing failed: {e}")

    state.preprocessed = preprocessed

    # Train
    engine = AutoBioEngine()
    try:
        results = engine.train_all(
            X_train=preprocessed["X_train"].values,
            y_train=preprocessed["y_train"],
            X_test=preprocessed["X_test"].values,
            y_test=preprocessed["y_test"],
            feature_names=preprocessed["feature_names"],
            class_names=preprocessed["class_names"],
            cv_folds=request.cv_folds,
            optimize_hyperparameters=request.optimize_hyperparameters,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")

    state.engine = engine

    # SHAP explainer (fit on training subset)
    explainer = ExplainabilityModule()
    try:
        background = preprocessed["X_train"].values[:min(200, len(preprocessed["X_train"]))]
        explainer.fit(engine.best_model, background, preprocessed["feature_names"])
        state.explainer = explainer
    except Exception as e:
        # Non-fatal: explainability might fail for some model/data combinations
        state.explainer = None

    state.is_trained = True
    save_state()

    comparison = engine.get_comparison_table()

    # Confusion matrix & Gene Network
    best_results = results[engine.best_model_name]
    cm_chart = ""
    network_chart = ""
    if state.explainer:
        try:
            cm_chart = state.explainer.plot_confusion_matrix(
                best_results["confusion_matrix"],
                preprocessed["class_names"],
            )
            # Fulfill the hackathon requirement for "Visualization of resistance gene networks"
            network_chart = state.explainer.generate_gene_network(
                preprocessed["X_train"], 
                preprocessed["feature_names"]
            )
        except Exception:
            pass

    return _numpy_safe({
        "status":               "trained",
        "best_model":           engine.best_model_name,
        "model_comparison":     comparison,
        "best_model_metrics":   {
            k: v for k, v in best_results.items()
            if k != "classification_report"
        },
        "classification_report": best_results["classification_report"],
        "dataset_info":          preprocessed["dataset_info"],
        "confusion_matrix_chart": cm_chart,
        "gene_network_chart":     network_chart,
    })


# ------------------------------------------------------------------
# 3. Global feature importance
# ------------------------------------------------------------------

@app.get("/explain/global")
def global_explanation(max_features: int = 15):
    """Return SHAP global feature importance for the best model."""
    if not state.is_trained:
        raise HTTPException(status_code=400, detail="Model not trained yet.")
    if state.explainer is None:
        # Fallback to built-in feature importances
        fi = state.engine.get_feature_importances()
        if not fi:
            raise HTTPException(status_code=500, detail="Explainability not available.")
        sorted_fi = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:max_features]
        return _numpy_safe({
            "top_features": [
                {"feature": k, "importance": v, "interpretation": ""}
                for k, v in sorted_fi
            ],
            "chart_base64": "",
            "explanation":  "Feature importances from the model's built-in scorer.",
        })

    try:
        X_test = state.preprocessed["X_test"].values
        result = state.explainer.global_importance(X_test[:min(200, len(X_test))], max_features)
        return _numpy_safe(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# 4. Single-sample prediction
# ------------------------------------------------------------------

@app.post("/predict")
def predict(request: PredictRequest):
    """Predict resistance for a single sample and return explanation + treatment."""
    if not state.is_trained:
        raise HTTPException(status_code=400, detail="Model not trained yet.")

    try:
        X = state.processor.encode_single_sample(request.features)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feature encoding error: {e}")

    prediction_result = state.engine.predict(X)

    # Local SHAP explanation
    local_exp = {}
    if state.explainer:
        try:
            local_exp = state.explainer.local_explanation(
                X, state.preprocessed["class_names"]
            )
        except Exception:
            pass

    # Extract detected genes from features
    detected_genes = [
        k for k, v in request.features.items()
        if k.lower().startswith("gene_") and v in (1, "1", True)
    ]

    treatment = recommend_treatment(
        prediction=prediction_result["prediction"],
        species=request.species,
        detected_genes=detected_genes,
        shap_top_features=local_exp.get("top_contributing_features", []),
    )

    return _numpy_safe({
        "prediction":     prediction_result,
        "explanation":    local_exp,
        "treatment":      treatment,
    })


# ------------------------------------------------------------------
# 5. Batch prediction
# ------------------------------------------------------------------

@app.post("/predict/batch")
def predict_batch(file: UploadFile = File(...)):
    """Accept a CSV of samples and return predictions for all rows."""
    if not state.is_trained:
        raise HTTPException(status_code=400, detail="Model not trained yet.")

    contents = file.file.read()
    try:
        df = pd.read_csv(__import__("io").BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    results = []
    for _, row in df.iterrows():
        sample = row.to_dict()
        try:
            X = state.processor.encode_single_sample(sample)
            pred = state.engine.predict(X)
            results.append({"sample": _numpy_safe(sample), **pred})
        except Exception as e:
            results.append({"sample": _numpy_safe(sample), "error": str(e)})

    return {"predictions": results, "total": len(results)}


# ------------------------------------------------------------------
# 6. Sample dataset info
# ------------------------------------------------------------------

@app.get("/sample-data")
def get_sample_data():
    """Return a preview of the built-in dataset."""
    sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample", "sample_amr_dataset.csv")
    try:
        df = pd.read_csv(sample_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "preview": _numpy_safe(df.head(10).to_dict(orient="records")),
        "columns": list(df.columns),
        "rows":    len(df),
    }


# ------------------------------------------------------------------
# 7. Model info
# ------------------------------------------------------------------

@app.get("/models/info")
def model_info():
    """Return current model state and comparison table."""
    if not state.is_trained:
        return {"is_trained": False}
    return _numpy_safe({
        "is_trained":       True,
        "best_model":       state.engine.best_model_name,
        "comparison_table": state.engine.get_comparison_table(),
        "feature_names":    state.engine.feature_names,
        "class_names":      state.engine.class_names,
    })
