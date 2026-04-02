# AutoBio-ResistAI: Deployment & Validation Guide 🚀

To ensure a seamless evaluation of AutoBio-ResistAI, please follow this simplified guide. This system is designed for high reliability across Docker and local Python environments.

---

## 1. Fast Deployment (Docker Recommended)
**Environment:** Linux, macOS, or Windows with Docker Desktop installed.

```bash
# 1. Clone & Navigate
git clone https://github.com/MeenalSinha/AutoBio-ResistAI.git
cd AutoBio-ResistAI-FULL

# 2. Add API Key (Optional for LLM assisted interpretations)
# Create a .env file in the root directory:
# OPENAI_API_KEY=your_key_here

# 3. Launch Full Stack
docker-compose up --build
```
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000

---

## 2. Manual Local Setup
**Prerequisites:** Python 3.10+, Node.js 18+.

### Backend (FastAPI)
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | Unix: source .venv/bin/activate
pip install --only-binary :all: -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (React/Vite)
```bash
cd frontend
npm install
npm run dev
```

---

## 3. Data Schema Validation (Critical for Custom Data) 📊
AutoBio-ResistAI uses an automated feature-mapping system. To ensure your custom datasets are parsed correctly by the engine, follow these naming conventions:

| Feature Type | Column Prefix | Format | Example |
| :--- | :--- | :--- | :--- |
| **Genetic Markers** | `gene_` | Binary (0 or 1) | `gene_mecA` |
| **MIC Phenotypes** | `mic_` | Numeric (float) | `mic_ampicillin` |
| **Species** | `species` | Categorical (string) | `E. coli` |
| **Target Label** | `resistance_class` | Categorical | `Resistant`, `Susceptible` |

*Note: The engine automatically handles missing values via Median/Mode imputation and aligns One-Hot encoding across train/test splits to prevent dimensional mismatch.*

---

## 4. Verification Checklist
- [ ] **API Connectivity:** Navigate to `http://localhost:8000/health`. You should see `{"status":"ok"}`.
- [ ] **Training Engine:** Upload a CSV and click "Run AutoBio Engine". Processing should take <15 seconds for sample data.
- [ ] **Visual Assets:** Ensure the "Resistance Gene Network" and "Confusion Matrix" appear in the Training tab after a successful run.
- [ ] **Predictive Inference:** Ensure the "Fill with Sample" button in the Predict tab correctly triggers a result with confidence scores.

---
**Technical Support:** For any mission-critical issues during evaluation, please consult `docs/architecture.md` or the `README.md`.
