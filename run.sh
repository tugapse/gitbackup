#!/bin/bash

# This script activates the Python virtual environment and runs main.py.
# All arguments passed to this script will be forwarded to main.py.

# "Source... thing": Activate the virtual environment
# This ensures that main.py runs with the correct Python interpreter and dependencies.
source .env/bin/activate

# Execute the main Python script, passing all arguments
python main.py "$@"

# Optional: Deactivate the virtual environment.
# For simple one-off runs like this, it's often omitted as the venv
# only affects this script's subshell, but it's good practice for longer sessions.
# deactivate