@echo off
REM Get the directory where the script itself is located
REM %~dp0 expands to the drive letter and path of the batch script.
SET "SCRIPT_DIR=%~dp0"

REM Execute the main.py script using 'python' (assumes python is in your PATH),
REM passing all arguments (%*) from this script to main.py
python "%SCRIPT_DIR%main.py" %*