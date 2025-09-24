@echo off
echo 🛡️ VacayMate Simple Defensive - Streamlit UI
echo =============================================
echo.
echo This version uses the WORKING app.py as base
echo with optional defensive monitoring added on top
echo.

REM Navigate to UI directory
cd /d "%~dp0UI"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

echo 🛡️ Starting Simple Defensive VacayMate UI...
echo 📍 URL: http://localhost:8503
echo 🔧 Features: Working app.py + Optional defensive monitoring
echo.

REM Run Streamlit app on different port
streamlit run simple_defensive_app.py --server.port 8503

echo.
echo Press any key to exit...
pause >nul
