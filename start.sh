#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# AutoBio-ResistAI — One-command launcher
# Starts both the FastAPI backend and the Vite dev frontend.
# ─────────────────────────────────────────────────────────────────────────────

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║       AutoBio-ResistAI Launcher             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Check Python ──────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.10+ first."
  exit 1
fi

# ── Check Node ────────────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
  echo "ERROR: node not found. Install Node.js 18+ first."
  exit 1
fi

# ── Backend setup ─────────────────────────────────────────────────────────
echo "[1/4] Installing backend dependencies..."
cd "$SCRIPT_DIR/backend"

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Create models directory
mkdir -p models

echo "[2/4] Starting FastAPI backend on http://localhost:8000 ..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "      Backend PID: $BACKEND_PID"

# ── Frontend setup ────────────────────────────────────────────────────────
echo "[3/4] Installing frontend dependencies..."
cd "$SCRIPT_DIR/frontend"
npm install --silent

echo "[4/4] Starting Vite dev server on http://localhost:5173 ..."
npm run dev &
FRONTEND_PID=$!
echo "      Frontend PID: $FRONTEND_PID"

# ── Summary ───────────────────────────────────────────────────────────────
echo ""
echo "  ✓ Backend  → http://localhost:8000"
echo "  ✓ API docs → http://localhost:8000/docs"
echo "  ✓ Frontend → http://localhost:5173"
echo ""
echo "  Press Ctrl+C to stop both servers."
echo ""

# ── Cleanup on exit ───────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID  2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  echo "Done."
}
trap cleanup EXIT INT TERM

# Keep script alive
wait
