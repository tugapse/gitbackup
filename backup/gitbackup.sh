#!/bin/bash
# This script automates Git operations: pull, add, commit, and push.
# It intelligently checks for local changes before attempting a commit.
# The script supports a --pull argument for pull-only operations.

# --- Configuration Variables ---
# Set the repository location. Can be overridden by the first command-line argument.
location="$1"
# Define the target branch name for pull and push operations.
branch_name="master"
# Flag to determine if only a Git pull operation should be performed.
# Initialized to 'false' and set to 'true' if '--pull' argument is provided.
do_pull=false

# --- Color Codes for Enhanced Output Readability ---
# Green color for success messages.
GREEN='\033[0;32m'
# Red color for error messages.
RED='\033[0;31m'
# No Color - Resets text color to default.
NC='\033[0m'

# --- Argument Parsing ---
# Loop through all provided command-line arguments.
while [[ $# -gt 0 ]]; do
  key="$1" # Store the current argument.
  case "$key" in
    --pull)
      # If '--pull' is found, set the flag to true and consume the argument.
      do_pull=true
      shift
      ;;
    *)
      # For any other argument, assume it's the repository location.
      # This allows the location to be specified after --pull, e.g., script.sh --pull /path/to/repo
      location="$1"
      shift
      ;;
  esac
done

# --- Determine Current Script Directory ---
# This ensures the script can find its own location robustly,
# even if called from a different working directory.
current_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

# --- Change to Repository Directory ---
# Prioritize the 'location' provided via argument.
# If no location is provided, default to the script's own directory.
if [ -n "$location" ]; then
  # Attempt to change to the specified repository directory.
  # If 'cd' fails, print an error and exit.
  cd "$location" || {
    echo -e "${RED}Error: Could not change to directory: $location${NC}" >&2
    exit 1 # Exit with a non-zero status to indicate failure.
  }
else
  # Attempt to change to the script's current directory.
  # If 'cd' fails, print an error and exit.
  cd "$current_dir" || {
    echo -e "${RED}Error: Could not change to directory: $current_dir${NC}" >&2
    exit 1
  }
fi

# --- Perform Git Pull (if --pull argument is present) ---
if $do_pull; then
  # Execute 'git pull' and pipe its output to 'tee'.
  # 'tee -a /tmp/git_log.txt' displays output to console AND appends to log file.
  git pull origin "$branch_name" 2>&1 | tee -a /tmp/git_log.txt
  # Inform the user that the pull operation is complete.
  echo -e "${GREEN}Git pull operation completed.${NC}"
  exit 0 # Exit the script immediately after a pull-only operation.
fi

# --- Check for Uncommitted Changes (Staged or Unstaged Tracked Files) ---
# This block now uses 'git diff-index --quiet HEAD' to reliably detect
# any changes in tracked files (modified, added, deleted, etc.),
# whether they are staged or unstaged.
if ! git diff-index --quiet HEAD --; then
  has_diffs=true
else
  has_diffs=false
fi

# --- Add, Commit, and Push Changes (if changes are detected) ---
if $has_diffs; then
  # Inform the user that changes have been detected.
  echo -e "${YELLOW}Changes detected. Adding and committing...${NC}"

  # Stage all changes in the current directory.
  git add . 2>&1 | tee -a /tmp/git_log.txt # Capture output, append to log.

  # Generate a unique timestamp for the commit message.
  timestamp=$(date +'%Y%m%d_%H%M%S')
  commit_message="Auto-commit_$timestamp"

  # Perform the Git commit.
  # The output is captured and appended to the log file.
  git commit -m "$commit_message" 2>&1 | tee -a /tmp/git_log.txt

  # Check the exit status of the 'git commit' command.
  if [ $? -eq 0 ]; then
    # If commit was successful, attempt to push.
    git push origin "$branch_name" 2>&1 | tee -a /tmp/git_log.txt
    # Check the exit status of the 'git push' command.
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}Successfully pushed to origin $branch_name${NC}"
    else
      # If push failed, print an error and exit.
      echo -e "${RED}Error: Push failed!${NC}" >&2
      exit 1 # Exit with a non-zero status.
    fi
  else
    # If commit failed, print an error and exit.
    echo -e "${RED}Error: Commit failed!${NC}" >&2
    exit 1 # Exit with a non-zero status.
  fi
else
  # If no changes were detected, inform the user and skip commit/push.
  echo -e "${YELLOW}No changes detected. Skipping commit.${NC}"
fi

# --- Script Completion ---
# Inform the user that the script has finished execution.
echo -e "${GREEN}Script finished.${NC}"
exit 0 # Exit with a zero status to indicate successful execution.
