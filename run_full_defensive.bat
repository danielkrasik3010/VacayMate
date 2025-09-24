@echo off
echo 🛡️ VacayMate Full Defensive System - Streamlit UI
echo ================================================
echo.
echo This version uses the COMPLETE defensive system with:
echo ✅ DefensiveVacayMate system (not original VacayMate)
echo ✅ Full state validation and emergency recovery
echo ✅ Circuit breaker protection for all APIs
echo ✅ Exponential backoff retry logic
echo ✅ Loop detection and prevention
echo ✅ Automatic fallback responses
echo ✅ Real-time health monitoring
echo ✅ Schema validation with Pydantic
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

echo 🛡️ Starting Full Defensive VacayMate UI...
echo 📍 URL: http://localhost:8504
echo 🔧 Features: Complete defensive system with all protection layers
echo.

REM Run Streamlit app on different port
streamlit run full_defensive_app.py --server.port 8504

echo.
echo Press any key to exit...
pause >nul
