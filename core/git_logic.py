import subprocess
import os
from core.logger import log # Ensure you're importing the log function

def run_git_command(repo_path, command_args, task_name, capture_output=False):
    """
    Helper function to run a git command.
    Logs command execution and output at 'normal' level, errors at 'error' level.
    """
    # This message will only show in verbose mode
    log(f"Executing Git command: {' '.join(command_args)} in '{repo_path}'", level='normal', task_name=task_name)
    try:
        process = subprocess.run(
            ["git"] + command_args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )

        if process.stdout:
            # Git STDOUT will only show in verbose mode
            log(f"Git STDOUT:\n{process.stdout.strip()}", level='normal', task_name=task_name)
        if process.stderr:
            # Git STDERR will only show in verbose mode, unless it's a critical error
            log(f"Git STDERR:\n{process.stderr.strip()}", level='normal', task_name=task_name)

        if process.returncode != 0:
            # Command failures are considered errors and will always be shown
            log(f"Git command FAILED with exit code {process.returncode}.", level='error', task_name=task_name)
            return None # Indicate failure
        return process.stdout.strip() if capture_output else True
    except FileNotFoundError:
        log(f"Error: 'git' command not found. Please ensure Git is installed and in your PATH.", level='error', task_name=task_name)
        return None
    except Exception as e:
        log(f"An unexpected error occurred while running Git command: {e}", level='error', task_name=task_name)
        return None

def pull_updates(repo_path, branch, task_name):
    """
    Performs a git pull on the specified branch and origin.
    Logs at 'normal' level for non-critical information.
    """
    # This message will only show in verbose mode
    log(f"Pulling updates for branch '{branch}'...", level='normal', task_name=task_name)
    result = run_git_command(repo_path, ["pull", "origin", branch], task_name)
    if result is None:
        log(f"Git Pull failed for branch '{branch}'.", level='error', task_name=task_name)
        return False
    # This message will only show in verbose mode
    log(f"Git Pull successful.", level='normal', task_name=task_name)
    return True

def diff_changes(repo_path, task_name):
    """
    Checks for any changes (modified, untracked, deleted, etc.) in the Git repository.
    Logs at 'normal' level for non-critical information.
    """
    # This message will only show in verbose mode
    log(f"Checking for pending changes using 'git status --porcelain'...", level='normal', task_name=task_name)
    output = run_git_command(repo_path, ["status", "--porcelain"], task_name, capture_output=True)

    if output is None:
        log(f"Error during Git status check.", level='error', task_name=task_name)
        return None
    elif output:
        # This message will only show in verbose mode
        log(f"Changes detected.", level='normal', task_name=task_name)
        return True
    else:
        # This message will only show in verbose mode
        log(f"No changes detected.", level='normal', task_name=task_name)
        return False

def add_commit_changes(repo_path, commit_message, files_to_add, task_name):
    """
    Stages specified files and commits them to the repository.
    Logs at 'normal' level for non-critical information.
    """
    # This message will only show in verbose mode
    log(f"Staging changes ('{files_to_add}')...", level='normal', task_name=task_name)
    add_result = run_git_command(repo_path, ["add", files_to_add], task_name)
    if add_result is None:
        log(f"Git Add failed.", level='error', task_name=task_name)
        return False

    # This message will only show in verbose mode
    log(f"Committing changes with message: '{commit_message}'...", level='normal', task_name=task_name)
    commit_result = run_git_command(repo_path, ["commit", "-m", commit_message], task_name)
    if commit_result is None:
        log(f"Git Commit failed.", level='error', task_name=task_name)
        return False

    # This message will only show in verbose mode
    log(f"Git Add and Commit successful.", level='normal', task_name=task_name)
    return True

def push_updates(repo_path, branch, origin, task_name):
    """
    Pushes committed changes to the specified remote origin and branch.
    Logs at 'normal' level for non-critical information.
    """
    # This message will only show in verbose mode
    log(f"Pushing changes to '{origin}/{branch}'...", level='normal', task_name=task_name)
    push_result = run_git_command(repo_path, ["push", origin, branch], task_name)
    if push_result is None:
        log(f"Git Push failed to '{origin}/{branch}'.", level='error', task_name=task_name)
        return False
    # This message will only show in verbose mode
    log(f"Git Push successful.", level='normal', task_name=task_name)
    return True