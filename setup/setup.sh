#!/bin/bash

# Image Compare Application Setup Script - PyQt6 Version
# This script sets up the Python virtual environment and installs dependencies

cd "$(dirname "$0")/.."

echo "Setting up Image Compare Application..."

# Check if system Python 3 is available
if ! command -v /usr/bin/python3 &> /dev/null; then
    echo "Error: System Python 3 is not available"
    echo "Please ensure macOS system Python is available"
    exit 1
fi

echo "Creating Python virtual environment with system Python 3..."
/usr/bin/python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing required packages..."
pip install -r setup/requirements.txt

echo ""
echo "Setup complete! You can now run the application with:"
echo ""
echo "./run.sh"
echo ""
echo "Or manually with:"
echo "source venv/bin/activate"
echo "python app/image_compare_pyqt.py"
