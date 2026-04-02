# AutoBio-ResistAI — Architecture Documentation

## System Overview

AutoBio-ResistAI is a full-stack antibiotic resistance prediction system comprising:

- A Python/FastAPI **backend** implementing the AutoBio ML engine
- A React/Vite **frontend** dashboard
- A Kaggle **notebook** for reproducible research
- A **SHAP** explainability layer
- An evidence-based **treatment recommendation** engine

---

## Data Flow

### Training Flow

```
User uploads CSV  ->  DataProcessor.load_from_bytes()
                  ->  DataProcessor.preprocess()
                       * auto-detect target column
                       * impute missing values
                       * one-hot encode categoricals
                       * StandardScaler
                       * train/test split (80/20, stratified)
                  ->  AutoBioEngine.train_all()
                       * LogisticRegression   (CV=5)
                       * RandomForestClassifier (CV=5)
                       * XGBClassifier         (CV=5)
                  ->  AutoBioEngine.select_best()  [by weighted F1]
                  ->  ExplainabilityModule.fit()
                       * TreeExplainer / KernelExplainer
                  ->  Return comparison table + metrics + CM plot
```

### Prediction Flow

```
User submits features  ->  DataProcessor.encode_single_sample()
                       ->  AutoBioEngine.predict()
                            * best_model.predict_proba()
                            * argmax -> label + confidence
                       ->  ExplainabilityModule.local_explanation()
                            * per-sample SHAP values
                       ->  treatment.recommend_treatment()
                            * gene detection
                            * species lookup
                            * urgency classification
                       ->  Return prediction + explanation + treatment
```

---

## API Endpoints

| Method | Endpoint           | Description                        |
|--------|--------------------|------------------------------------|
| GET    | /health            | AI system health + training status       |
| POST   | /upload            | Upload real CSV/Excel dataset      |
| POST   | /train             | Run Automated ML Engine            |
| GET    | /explain/global    | Global SHAP feature importance     |
| POST   | /predict           | AI-assisted resistance prediction   |
| POST   | /predict/batch     | Batch CSV resistance prediction    |
| GET    | /sample-data       | Real AMR dataset sample preview     |
| GET    | /models/info       | AI model state + comparison         |

---

## Models Used

| Model               | Library      | Key Hyperparameters                         |
|---------------------|--------------|---------------------------------------------|
| Logistic Regression | scikit-learn | C=1.0, max_iter=1000, lbfgs                 |
| Random Forest       | scikit-learn | n_estimators=200, max_depth=10              |
| XGBoost (Optimized) | xgboost      | n_estimators, max_depth, lr (Bayesian)     |

### Bayesian Optimization (Optuna)
AutoBio-ResistAI leverages **Optuna** to execute a Bayesian search across the hyperparameter space for the XGBoost champion model. 
- Objective function: Maximise Weighted F1 score using 5-fold Stratified K-Fold cross-validation.
- Parameter space: `n_estimators`, `max_depth`, `learning_rate`, `subsample`, and `colsample_bytree`.
- Persistence: Optimized model weights and hyperparameters are persisted via `joblib` for zero-latency inference after restart.

Selection criterion: Weighted F1 Score on hold-out test set (20% stratified split).
Cross-validation: 5-fold StratifiedKFold.

---

## Explainability

- TreeExplainer (exact, fast) used for Random Forest and XGBoost
- KernelExplainer (model-agnostic) used for Logistic Regression
- SHAP values computed on background sample of up to 200 test instances
- Global importance = mean absolute SHAP values across all test samples and classes
