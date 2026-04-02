# Saved Models

This directory contains model artefacts saved by the AutoBio Engine.

## Pre-trained artefacts (from Kaggle run 6)

| File | Description |
|------|-------------|
| `best_model.joblib` | XGBClassifier champion — F1=0.9827, ROC=0.9985 |
| `scaler.joblib` | StandardScaler fitted on 10,710 training samples |
| `feature_names.json` | 32 selected feature names (in order) |
| `model_report.json` | Full performance metrics |

The backend loads these automatically if they exist.
After `/train` is called, new artefacts are written here.

## Runtime artefacts (created by /train)

| File | Created by |
|------|------------|
| `engine.joblib` | Full AutoBioEngine state |
| `best_model.joblib` | Overwritten with newly trained model |
