@echo off
REM Image Compare Application Setup Script - PyQt6 Version
REM This script sets up the Python virtual environment and installs dependencies

cd /d "%~dp0.."

echo Setting up Image Compare Application...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not available or not in PATH
    echo Please install Python 3.x and ensure it's in your system PATH
    pause
    exit /b 1
)

echo Creating Python virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing required packages...
pip install -r setup\requirements.txt

echo.
echo Setup complete! You can now run the application with:
echo.
echo run.bat
echo.
echo Or manually with:
echo venv\Scripts\activate.bat
echo python app\image_compare_pyqt.py

pause
