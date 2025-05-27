@echo off
REM This script activates the Python virtual environment and runs main.py.
REM All arguments passed to this script will be forwarded to main.py.

REM "Source... thing": Activate the virtual environment
REM Using 'call' is important so the script continues after activation.
call .env\Scripts\activate.bat

REM Execute the main Python script, passing all arguments
python main.py %*

REM Optional: Deactivate the virtual environment.
REM For simple one-off runs like this, it's often omitted as the venv
REM only affects this script's context, but it's good practice for longer sessions.
REM call deactivate.bat