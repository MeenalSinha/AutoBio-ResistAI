# AutoBio-ResistAI

**A self-optimizing AI system for antibiotic resistance prediction**  
F1 = 0.9827 | ROC-AUC = 0.9985 | Trained on 10,710 real clinical isolates

---

## Folder Structure

```
AutoBio-ResistAI/
├── README.md                    ← This file
├── start.sh                     ← One-command launcher (backend + frontend)
├── .gitignore
│
├── backend/                     ← FastAPI Python backend
│   ├── main.py                  ← 8 REST endpoints
│   ├── autobio_engine.py        ← AutoML: LR + RF + XGBoost, auto-select
│   ├── data_processor.py        ← Load, impute, encode, scale, split
│   ├── explainability.py        ← SHAP TreeExplainer / KernelExplainer
│   ├── treatment.py             ← Gene→drug mapping, species recommendations
│   ├── requirements.txt
│   └── models/                  ← Pre-trained artefacts + runtime saves
│       ├── best_model.joblib    ← XGBoost champion (593 KB)
│       ├── scaler.joblib        ← StandardScaler
│       ├── feature_names.json   ← 32 selected features
│       └── model_report.json    ← Performance metrics
│
├── frontend/                    ← React 18 + Vite + Recharts
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── App.jsx + App.module.css
│       ├── index.css            ← Light theme with CSS variables
│       ├── utils/api.js         ← All Axios calls to backend
│       ├── components/          ← Sidebar, Card, Button, Alert, StatTile, PageHeader
│       └── pages/
│           ├── Dashboard.jsx    ← Overview, API status, dataset links
│           ├── TrainPage.jsx    ← Upload, run engine, comparison chart + table
│           ├── PredictPage.jsx  ← Feature form, radar chart, SHAP, treatment
│           ├── ExplainPage.jsx  ← Global SHAP bar + interpretation table
│           └── TreatmentPage.jsx← Full antibiotic guidance with gene mechanisms
│
├── notebooks/                   ← Kaggle submission notebook
│   ├── AutoBio_ResistAI_UNBEATABLE.ipynb  ← Upload this to Kaggle
│   └── AutoBio_ResistAI_UNBEATABLE.py     ← Same code as Python source
│
├── data/
│   ├── datasets/                ← Real clinical datasets
│   │   ├── Bacteria_dataset_Multiresictance.csv  ← 10,710 rows (primary)
│   │   └── Antimicrobial_Resistance_Dataset.xlsx ← 274 rows (secondary)
│   └── sample/                  ← Quick-start test data
│       └── sample_amr_data.csv  ← 20-row demo CSV for /predict/batch
│
└── docs/
    └── architecture.md          ← System design + API reference
```

---

## Quick Start

### Requirements
- Python 3.10+
- Node.js 18+

### One command
```bash
chmod +x start.sh
./start.sh
```

Opens:
- **Frontend** → http://localhost:5173
- **Backend**  → http://localhost:8000
- **API docs** → http://localhost:8000/docs

### Manual startup

**Backend:**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Check API status + model state |
| GET | `/sample-data` | Preview built-in synthetic data |
| GET | `/models/info` | Current model + comparison table |
| POST | `/upload` | Upload CSV/Excel dataset |
| POST | `/train` | Run AutoBio Engine (train all models) |
| GET | `/explain/global` | SHAP global feature importance |
| POST | `/predict` | Single-sample resistance prediction |
| POST | `/predict/batch` | Batch predictions from CSV |

---

## Key Results (Kaggle notebook)

| Model | F1 | ROC-AUC | PR-AUC | Recall(R) |
|-------|----|---------|--------|-----------|
| Logistic Regression (tuned) | 0.9488 | 0.9928 | 0.8779 | 0.9384 |
| Random Forest (tuned) | 0.9819 | 0.9985 | 0.9541 | 0.9315 |
| **XGBoost (tuned)** | **0.9827** | 0.9985 | **0.9590** | 0.9418 |
| Soft Voting Ensemble | 0.9826 | **0.9988** | **0.9650** | 0.9384 |

Top feature: `total_mic_burden` (SHAP=0.973, consensus 4/4 models)  
Strongest single biomarker: cefazolin MIC (Cohen's d=+1.498***)

---

## Compatibility Notes

This codebase was audited and fixed for:
- **XGBoost ≥2.0** — `use_label_encoder` param removed (was deprecated)
- **SHAP ≥0.45** — SHAP values normalisation handles both old (list) and new (3D array) formats
- **Memory safety** — `n_jobs=1` throughout (safe for containerised deployments)
- **OHE alignment** — `encode_single_sample()` reindexes to training columns, preventing feature mismatch on predict
- **Class imbalance** — `class_weight="balanced"` on LR and RF

---

*Research and educational purposes only. All treatment decisions require validated laboratory susceptibility testing and clinical judgement.*
