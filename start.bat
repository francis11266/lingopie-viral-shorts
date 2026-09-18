@echo off
REM ---- Lingopie Viral Shorts : double-click to launch the web app (Windows) ----
cd /d "%~dp0"
where python >nul 2>nul || (echo Please install Python 3.11+ from python.org, then run again. & pause & exit /b)
where node   >nul 2>nul || (echo Please install Node.js 18+ from nodejs.org, then run again. & pause & exit /b)

if not exist ".venv" (
  echo Setting up (first run only)...
  python -m venv .venv
  call .venv\Scripts\activate
  pip install --quiet --upgrade pip
  pip install --quiet -r requirements.txt
  call npm install --silent
) else (
  call .venv\Scripts\activate
)

if not exist ".env" ( copy /y ".env.example" ".env" >nul & echo Created .env - open it and paste your two API keys, then run this again. & notepad .env & pause & exit /b )

echo Starting... your browser will open at http://localhost:8000
start "" http://localhost:8000
python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
pause
