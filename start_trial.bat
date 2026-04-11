@echo off
echo Starting Options Quant Trading Trial...

echo Stopping any existing instances...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1

echo Starting Backend Server (FastAPI)...
start cmd /k ".\venv\Scripts\activate.bat && uvicorn backend.main:app --host 127.0.0.1 --port 8000"

echo Starting Frontend Server (Vite/React)...
cd frontend
start cmd /k "npm run dev"

echo Boot Sequence Complete. Please wait ~5 seconds for servers to initialize.
echo The UI will be available at http://localhost:5173
