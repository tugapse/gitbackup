#!/bin/bash

# This script builds a standalone executable for Linux/macOS using PyInstaller.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Starting PyInstaller Build (Linux/macOS) ---"

# 1. Activate the virtual environment
echo "Activating virtual environment..."
if [ -f ".env/bin/activate" ]; then
    source .env/bin/activate
    echo "Virtual environment activated."
else
    echo "Error: Virtual environment 'venv' not found. Please create it (python3 -m venv venv) and install dependencies (pip install -r requirements.txt) first."
    exit 1
fi

# 2. Clean previous build artifacts
echo "Cleaning previous build artifacts..."
rm -rf build dist *.spec

# 3. Run PyInstaller
# --name "GitAutomator": Sets the name of the executable.
# --onefile: Creates a single executable file (recommended for distribution).
#            Use --onedir instead if you prefer a directory with the executable and dependencies (easier for debugging).
# --clean: Cleans PyInstaller cache and temporary files.
# --add-data "core:core": Includes the 'core' directory. Format is SOURCE:DEST_IN_BUNDLE (Linux/macOS uses ':').
# main.py: Your main script file.
echo "Running PyInstaller..."
pyinstaller --name "GitAutomator" \
            --onefile \
            --clean \
            --add-data "core:core" \
            main.py

# 4. Deactivate virtual environment (optional, but good practice)
deactivate
echo "Virtual environment deactivated."

echo "--- PyInstaller Build Complete ---"
echo "Your executable is located in: dist/GitAutomator"
echo "You can run it from anywhere: ./dist/GitAutomator"
