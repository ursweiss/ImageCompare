@echo off
REM Image Compare Application Launcher - PyQt6 Version
REM This script activates the virtual environment and runs the modern PyQt6 image comparison app

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Please run setup first:
    echo setup\setup.bat
    pause
    exit /b 1
)

echo Starting Image Compare Application...
call venv\Scripts\activate.bat
python3 app\image_compare_pyqt.py
