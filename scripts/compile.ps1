# This script builds a standalone executable for Windows using PyInstaller.

Write-Output "--- Starting PyInstaller Build (Windows) ---"

# 1. Activate the virtual environment
Write-Output "Activating virtual environment..."

$activateScript = ".\.venv\Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    & $activateScript
    Write-Output "Virtual environment activated."
} else {
    Write-Error "Virtual environment '.venv' not found. Please create it (python -m venv .venv) and install dependencies (pip install -r requirements.txt) first."
    exit 1
}

# 2. Clean previous build artifacts
Write-Output "Cleaning previous build artifacts..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
Get-ChildItem -Filter "*.spec" | Remove-Item -Force

# 3. Run PyInstaller
Write-Output "Running PyInstaller..."

pyinstaller --name "GitB" `
            --onefile `
            --clean `
            --add-data "core;core" `
            main.py

# 4. Deactivate virtual environment
if (Get-Command deactivate -ErrorAction SilentlyContinue) {
    deactivate
    Write-Output "Virtual environment deactivated."
}

Write-Output "--- PyInstaller Build Complete ---"
Write-Output "Your executable is located in: dist\GitB.exe"