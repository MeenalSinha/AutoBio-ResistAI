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
| GET    | /health            | API health + training status       |
| POST   | /upload            | Upload dataset file                |
| POST   | /train             | Run AutoBio Engine                 |
| GET    | /explain/global    | Global SHAP feature importance     |
| POST   | /predict           | Single-sample prediction           |
| POST   | /predict/batch     | Batch CSV prediction               |
| GET    | /sample-data       | Synthetic dataset preview          |
| GET    | /models/info       | Model state + comparison           |

---

## Models Used

| Model               | Library      | Key Hyperparameters                         |
|---------------------|--------------|---------------------------------------------|
| Logistic Regression | scikit-learn | C=1.0, max_iter=1000, lbfgs                 |
| Random Forest       | scikit-learn | n_estimators=200, max_depth=10              |
| XGBoost             | xgboost      | n_estimators=200, max_depth=6, lr=0.1       |

Selection criterion: Weighted F1 Score on hold-out test set (20% stratified split).
Cross-validation: 5-fold StratifiedKFold.

---

## Explainability

- TreeExplainer (exact, fast) used for Random Forest and XGBoost
- KernelExplainer (model-agnostic) used for Logistic Regression
- SHAP values computed on background sample of up to 200 test instances
- Global importance = mean absolute SHAP values across all test samples and classes
