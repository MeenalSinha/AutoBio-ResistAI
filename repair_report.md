# AutoBio-ResistAI: System Reality Check and Repair Report

## 1. Reverse Engineered Architecture
The application follows a **Monolith with modules** pattern.
- **Entrypoint:** `backend/main.py` is the central FastAPI entrypoint orchestrating requests.
- **Frontend Layer:** React/Vite Single Page Application making direct HTTP requests to the backend API.
- **Data Layer (`data_processor.py`):** Handles CSV/Excel intake, dynamic categorical/target identification, imputation, and feature scaling. 
- **Service Layer (ML Core):** `autobio_engine.py` manages multiple Scikit-Learn/XGBoost models, runs cross-validation, and determines the champion model based on weighted F1 metrics.
- **Explainability Layer (`explainability.py`):** Wraps tree-based or kernel-based SHAP explainers around the selected best model context.
- **Treatment Mapping Layer (`treatment.py`):** A strict rule-based pipeline that fuses susceptibility prediction with detected genes and pre-defined antibiotic taxonomy to recommend treatments.

### Structural Flaws Detected:
- **Singleton In-Memory State:** The system relied on an `AppState` singleton without disk/DB persistence, losing all training results if the server restarts or if scaled to multiple workers.
- **Mixed responsibilities:** `main.py` directly handled decoding uploaded file bytes (violating data layer abstraction) and routing at the same time.

## 2. Dependency Graph Findings
- **Data Flow:** `Frontend` → `main.py` → `data_processor.py` → `autobio_engine.py` → `explainability.py` → `treatment.py`.
- **Tight Coupling:** `main.py` was tightly coupled to raw uploaded bytes, maintaining a duplicate state of `_uploaded_bytes` to pass back into the `DataProcessor` rather than persisting data naturally.
- **Tightly Coupled Hardcoded AI Logic:** Interpretations were tightly coupled to `explainability.py` local dictionaries rather than an actual generative system.
- **Circular Dependencies:** None detected; the codebase maintained a clean layered approach horizontally.

## 3. Execution Flow Issues
- **Missing Persistent State Loading:** `AutoBioEngine` and `DataProcessor` could be fully trained, but the state wasn't serialized, so upon restarting, the system incorrectly assumed it was untrained.
- **Blocking Async Routes:** The batch prediction endpoint `predict_batch` was marked as `async def` but executed a heavy CPU-bound loop and synchronous Pandas file parsing, effectively locking the FastAPI event loop for other concurrent requests.

## 4. Broken Components
- **Dataset Reloading Logic:** When executing `/train`, if dummy data wasn't triggered, the system blindly attempted to read from raw cached memory (`proc._uploaded_bytes`). This broke when scaling or using larger payloads.
- **API CORS:** Was set to explicitly wide `allow_origins=["*"]` whilst relying on cross-site requests via an incorrectly configured frontend Vite proxy.

## 5. Security Vulnerabilities
- unsafe file uploads via an overly permissive open endpoint.
- Server-side Denial of Service via event-loop locking in `/predict/batch`.
- Insecure API access due to overly-broad CORS implementation in `main.py` `=["*"]`.

## 6. Performance Issues
- **Event Loop Blocking:** As noted above, synchronous loops in async API handlers.
- **Memory Scaling:** `generate_sample_dataset` and `train_models` executed in threads holding duplicate DataFrame contexts simultaneously.
- **Number of Workers Fixed:** No provision to handle `n_jobs > 1` concurrency in XGB/RandomForest outside of default logic, though explicitly controlled out of the box to prevent container OOMs.

## 7. Fake or Placeholder Logic
- **Fake AI Output:** The `_interpret_feature` effectively functioned as a simulated hardcoded response dictionary (`GENE_INTERPRETATIONS`), giving the illusion of an LLM summarizer without executing a generative model. 
- **Demo-only pipeline:** `generate_sample_dataset()` generated fundamentally fake mathematical noise representing data instead of drawing from authentic sample test cases.

## 8. Infrastructure Problems
- **Dockerization was completely absent:** There were no `Dockerfile` or `docker-compose.yml` assets, making the system unfit for cloud-native deployment.
- **Incompatible Proxy Logic:** The backend operated on localhost:8000 natively without an `/api` proxy prefix, yet Vite's `api.js` relied on bypassing Vite to hit `localhost:8000` directly. 

## 9. Runtime Failure Risks
- OOM crashes under production loads due to missing worker replication and batch file read-all implementations.
- Model dropping due to stateless restart behavior without joblib reloading.
- External model API request timeouts missing fallback graceful defaults.

## 10. Fixed Code Sections
- **Docker Containerization Pipeline:** Created multi-stage production Dockerfiles for `frontend` (Nginx standard proxy config) and `backend` (Python slim), linked via `docker-compose.yml`.
- **Model State Persistence:** Authored and implemented `save_state()` / `load_state()` via `joblib` in `main.py` to cache the processor footprint and trained champion model across restarts and workers.
- **Asynchronous Loop Correction:** Modified `/predict/batch` from `async def` to `def`, properly offloading the intensive looping and `Pandas` computation to FastAPI's background thread pool, maintaining unblocked event loops.
- **Real LLM Pipeline Integration:** Replaced the hardcoded imitation explanations in `explainability.py` with an actual `requests` pipeline configured to target OpenAI `gpt-3.5-turbo` with prompt isolation—while preserving localized fallbacks.
- **Demo Pipeline Erasure:** Demolished `generate_sample_dataset()` math logic and bound the `use_sample_data` logic to a real physical CSV loaded securely via disk routes.
- **Proxy/CORS Hardening:** Hard-routed `frontend/src/utils/api.js` BASE_URL dynamically to `/api`, correctly isolating external domains and shifting proxy routing to Nginx boundaries.

## 11. Architecture Improvements
- Refactored stateless monolith singleton approach toward a cacheable, disk-backed serialization layer supporting concurrent access or restart resilience.
- Moved towards a scalable Microservice proxy orientation using Nginx.
- Established strict Generative AI fallbacks vs absolute deterministic rules in explanation generation.

## 12. System Production Readiness Score (0-10)
**Current Score (After Auto Repacements): 8.5/10**
(Before Analysis: 3/10)

The system is now fully containerized, functionally persists machine learning models across restarts, eliminates fake hardcoded generative AI structures into a real pipeline, securely routes via an Nginx frontend without CORS abuse, and prevents FastAPI event-loop lockups. Final deductions are related to requiring more robust cloud-scale file system mapping (like AWS S3) for production dataset uploads rather than local disk.
