#!/bin/bash

# Get the directory where the script itself is located
# dirname "$0" gets the directory of the script
# readlink -f resolves any symlinks and gives the absolute path
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Execute the main.py script using python3,
# passing all arguments ($@) from this script to main.py
python3 "${SCRIPT_DIR}/main.py" "$@"