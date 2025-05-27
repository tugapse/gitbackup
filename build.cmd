@echo off
REM This script builds a standalone executable for Windows using PyInstaller.

echo --- Starting PyInstaller Build (Windows) ---

REM 1. Activate the virtual environment
echo Activating virtual environment...
@REM if exist ".env\Scripts\activate.bat" (
@REM     call .env\Scripts\activate.bat
@REM     echo Virtual environment activated.
@REM ) else (
@REM     echo Error: Virtual environment 'venv' not found. Please create it (python -m venv venv) and install dependencies (pip install -r requirements.txt) first.
@REM     exit /b 1
@REM )

REM 2. Clean previous build artifacts
echo Cleaning previous build artifacts...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del /q *.spec

REM 3. Run PyInstaller
REM --name "GitAutomator": Sets the name of the executable.
REM --onefile: Creates a single executable file (recommended for distribution).
REM            Use --onedir instead if you prefer a directory with the executable and dependencies (easier for debugging).
REM --clean: Cleans PyInstaller cache and temporary files.
REM --add-data "core;core": Includes the 'core' directory. Format is SOURCE;DEST_IN_BUNDLE (Windows uses ';').
REM main.py: Your main script file.
echo Running PyInstaller...
pyinstaller --name "GitAutomator" ^
            --onefile ^
            --clean ^
            --add-data "core;core" ^
            main.py

REM 4. Deactivate virtual environment (optional, but good practice)
if exist "venv\Scripts\deactivate.bat" (
    call venv\Scripts\deactivate.bat
    echo Virtual environment deactivated.
)

echo --- PyInstaller Build Complete ---
echo Your executable is located in: dist\GitAutomator.exe
echo You can run it from anywhere: .\dist\GitAutomator.exe