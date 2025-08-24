#!/bin/bash

# Image Compare Application Launcher - PyQt6 Version
# This script activates the virtual environment and runs the modern PyQt6 image comparison app

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup first:"
    echo "./setup/setup.sh"
    exit 1
fi

echo "Starting Image Compare Application..."
source venv/bin/activate
python3 app/image_compare_pyqt.py
