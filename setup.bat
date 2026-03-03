@echo off
REM Quick setup script for Agentic OER Finder (Windows)
REM This script sets up both backend and frontend for development

echo.
echo ====================================
echo Agentic OER Finder - Quick Setup
echo ====================================
echo.

REM Backend Setup
echo Installing Python backend...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

echo Backend setup complete!
echo.

REM Frontend Setup
echo Installing React frontend...
cd frontend

echo Installing Node dependencies...
call npm install

echo Frontend setup complete!
echo.

echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo To run the application:
echo.
echo Terminal 1 - Backend:
echo   venv\Scripts\activate.bat
echo   python run.py
echo.
echo Terminal 2 - Frontend:
echo   cd frontend
echo   npm run dev
echo.
echo Then visit: http://localhost:3000
echo.
echo For more information, see README.md
echo.
pause
