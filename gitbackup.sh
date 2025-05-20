#!/bin/bash
# This script automates git pull, add, and commit operations.
# It checks for local changes before committing.
# It now accepts a --pull argument to only run git pull

# Set the repository location (you can change this via command line)
location="$1" # first argument
branch_name="master"          # Default branch name is master
do_pull=false                # Initialize do_pull to false

# Define color codes for more readable output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case "$key" in
    --pull)
      do_pull=true
      shift # Remove --pull from the arguments list
      ;;
    *)    # Default case: assume it's the location
      location="$1"
      shift # Remove the argument
      ;;
  esac
done

# Get the current directory of the script.  This is more robust.
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

# Change to the repository directory
if [ -n "$location" ]; then # Only cd if location is not empty
  cd "$location" || {
    echo -e "${RED}Error: Could not change to directory: $location${NC}" >&2
    exit 1 # Use exit code 1 for general errors
  }
else
  cd "$current_dir" || { # change to the directory of the script
    echo -e "${RED}Error: Could not change to directory: $current_dir${NC}" >&2
    exit 1
  }
fi

# Git pull
if $do_pull; then
  git pull origin "$branch_name" 2>&1 | tee -a /tmp/git_log.txt # Capture output, append to log
  echo -e "${GREEN}Git pull operation completed.${NC}"
  exit 0 # Exit the script after the pull
fi

# Check for uncommitted changes using git diff
  if ! git diff --quiet; then # check for unstaged changes
    has_diffs=true
  else
    has_diffs=false
  fi


# Add and commit if there are changes
if $has_diffs; then
  git add . 2>&1 | tee -a /tmp/git_log.txt # Capture output

  # Generate timestamp for the commit message
  timestamp=$(date +'%Y%m%d_%H%M%S')
  commit_message="Auto-commit_$timestamp"

  # Capture the output of git commit
  git commit -m "$commit_message" 2>&1 | tee -a /tmp/git_log.txt # Capture output, append to log

  if [ $? -eq 0 ]; then
    git push origin "$branch_name" 2>&1 | tee -a /tmp/git_log.txt
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}Successfully pushed to origin $branch_name${NC}"
    else
      echo -e "${RED}Error: Push failed!${NC}" >&2
      exit 1 # Exit on push failure
    fi
  else
    echo -e "${RED}Error: Commit failed!${NC}" >&2
    exit 1 # Exit if commit failed.  Important for automation.
  fi
fi

echo -e "${GREEN}Script finished.${NC}"
exit 0 # Explicitly exit with success code
