#!/bin/bash
# ---- Lingopie Viral Shorts : double-click to launch the web app (macOS/Linux) ----
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Install Python 3.11+ from python.org, then run again."; read -r _; exit 1; }
command -v node    >/dev/null || { echo "Install Node.js 18+ from nodejs.org, then run again."; read -r _; exit 1; }

if [ ! -d ".venv" ]; then
  echo "Setting up (first run only)…"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt
  npm install --silent
else
  source .venv/bin/activate
fi

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env — open it, paste your two API keys, then run this again."
  open .env 2>/dev/null || nano .env
  exit 0
fi

echo "Starting… opening http://localhost:8000"
( sleep 2; open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null ) &
python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
