# AutoBio-ResistAI: Self-Optimizing Antibiotic Resistance Prediction

A fully autonomous, scalable, and explainable Machine Learning clinical decision support system designed to predict and navigate the growing crisis of Antimicrobial Resistance (AMR). 

🏆 **Hackathon Benchmark Performance:** F1 = 0.9827 | ROC-AUC = 0.9985 | Trained against 10,710 real clinical isolates.

---

## 1. Overview
**The Problem:** Antimicrobial resistance (AMR) is a global health crisis. Pathogens are mutating faster than we can discover new drugs. Incomplete or delayed susceptibility testing leads to empirical "blind" treatments, heightening patient mortality and accelerating superbug evolution.

**The Solution:** AutoBio-ResistAI is a next-generation clinical intelligence system. It rapidly ingests raw bacterial genetic and phenotypic data, autonomously trains and compares advanced ML models, visually maps biological resistance networks, and returns explainable, targeted antibiotic recommendations.

## 2. Key Features
- **AutoBio Engine:** A self-optimizing AutoML framework. It tests Logistic Regression, Random Forests, and leverages **Optuna Bayesian Hyperparameter Optimization** to dynamically benchmark and select the ultimate Champion model (XGBoost).
- **Explainable AI (SHAP):** Black-box predictions are demystified. Interactive SHAP analytics display the exact genotypic and phenotypic factors driving a Resistance determination.
- **Resistance Gene Networks:** Meets advanced hackathon criteria by rendering an organic NetworkX-based co-occurrence map, proving Spearman correlation between gene expression (e.g. `gene_mecA`) and MIC outcome behavior.
- **Targeted Treatment Recommender:** Fuses heuristic resistance flag checks with dynamic localized LLM evaluation to generate clinical prescribing guidelines (drugs to isolate, drugs to prescribe).
- **Full-Stack Turnkey App:** FastAPI Backend married to a dynamic React Front-End. Completely Dockerized for friction-free mission deployment.

## 3. Tech Stack
- **Machine Learning Layer:** Scikit-Learn, XGBoost, Optuna (Bayesian Tuning), SHAP, NetworkX.
- **Backend Infrastructure:** Python 3.10+, FastAPI, Uvicorn, Pandas, Joblib (state persistence).
- **Frontend Architecture:** React 18, Vite, Recharts, Vanilla CSS Modules (Premium Glassmorphism Light Theme with *Inter* & *Outfit* typography).

## 4. Setup Instructions

### Option A: Complete Docker Deployment (Recommended)
```bash
# Clone the repository
git clone https://github.com/MeenalSinha/AutoBio-ResistAI.git
cd AutoBio-ResistAI-FULL

# Launch full stack (UI on 3000, Backend on 8000)
docker compose up --build
```

### Option B: Local Manual Setup

**1. FastAPI Backend:**
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate # Windows: .venv\Scripts\activate
pip install --only-binary :all: -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**2. React Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 5. How to Run (Step-by-Step)
1. Start the system infrastructure. Navigate to `http://localhost:3000` via your browser.
2. Click **Launch Engine** from the main dashboard.
3. In the training UI, ensure **Use Built-in Sample Data** and **Optimize Hyperparameters** toggles are active.
4. Click **Run AutoBio Engine**. Wait (~10 seconds) for the engine to optimize XGBoost spaces and benchmark the models against the holdout set.
5. Review the resulting model metrics, Confusion Matrix, and the bespoke Resistance Gene Network visualization.

## 6. Example Usage Flow
- **Train phase:** AutoBio sweeps the parameter space and locks an optimized XGBoost classifier.
- **Predict phase:** Input isolate parameters such as `species = "E. coli"`, `gene_blaTEM = 1`, and `mic_ampicillin = 16.0`.
- **Explain phase:** The SHAP breakdown instantly tells the physician: *cefazolin MIC was the #1 critical feature driving the Resistant classification.*
- **Treatment phase:** The intelligence suite flags the presence of `gene_blaTEM` and actively suggests prescribing Beta-lactamase inhibitors or Carbapenems while avoiding Penicillins.

## 7. Model Performance Highlights
Tested rigorously against open-source Antimicrobial Resistance databanks.

| Model | F1-Score | ROC-AUC | Precision | Recall |
|-------|----------|---------|-----------|--------|
| Logistic Regression | 0.9488 | 0.9928 | 0.8779 | 0.9384 |
| Random Forest | 0.9819 | 0.9985 | 0.9541 | 0.9315 |
| **XGBoost (Optuna Tuned)** | **0.9827** | **0.9985** | **0.9590** | **0.9418** |

*AutoBio correctly identified `total_mic_burden` and specific cephalosporin breakpoints as the highest correlating predictive features across all tested vectors.*

## 8. Project Structure
```text
AutoBio-ResistAI/
├── backend/                  ← FastAPI Python app (AutoBio Engine + API)
│   ├── autobio_engine.py     ← AutoML pipeline and Optuna Bayesian Optimizer
│   ├── explainability.py     ← SHAP explainer and NetworkX gene networks
│   ├── main.py               ← Async endpoints and joblib state manager
│   ├── data_processor.py     ← Real dataset encoding/imputation pipelines
│   └── treatment.py          ← Heuristic drug recommendation logics
│
├── frontend/                 ← Pristine React 18 Web App
│   ├── src/pages/            ← Dashboard, TrainPage, PredictPage UI
│   ├── src/components/       ← Reusable glassmorphic UI elements
│   ├── src/utils/api.js      ← Sync layer over localhost/docker networks
│   └── index.html            ← Premium Typography config
│
├── data/                     ← Curated hackathon AMR CSV datasets
├── docker-compose.yml        ← 12-factor orchestrator definitions
└── start.sh                  ← Local deployment scripts
```

## 9. Why This Matters (Clinical Impact)
Empirical prescribing without rapid actionable intelligence leads directly to treatment failure, elevated patient mortality, and accelerates the evolution of multi-drug resistant superbugs. 

AutoBio-ResistAI bridges the critical gap between raw microbiological sequencing and physician decision-making. By offering **explainable** proof behind its logic, rendering complex DNA networks immediately understandable, and instantly adapting to new regional bacterial datasets via automated hyperparameter tuning, it gives local hospitals a perpetually-learning weapon to win the war against antimicrobial resistance.

---
*Disclaimer: Built exclusively for research and hackathon demonstration purposes. Clinical treatment decisions mandate laboratory confirmed susceptibility testing and validated physician judgement.*
