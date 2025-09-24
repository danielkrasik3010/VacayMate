@echo off
echo 🛡️ VacayMate Defensive System Launcher
echo =====================================
echo.

REM Navigate to code directory
cd /d "%~dp0code"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

echo 🚀 Starting Defensive VacayMate System...
echo.

REM Run the defensive system
python run_defensive_vacaymate.py

echo.
echo 🎉 System execution completed!
echo Press any key to exit...
pause >nul
