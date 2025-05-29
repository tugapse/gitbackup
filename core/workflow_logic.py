import os
import sys
from datetime import datetime
from core.logger import log
from core.command_logic import execute_command

from core.git_logic import (
    initialize_repo,
    checkout_or_create_branch,
    pull_updates,
    diff_changes,
    add_commit_changes,
    push_updates
)


def run_task_workflow(args, task, config_file_path):
    """
    Executes the full Git automation workflow for a given task.
    """
    log(f"Starting automated task from '{config_file_path}'", level='step')

    task_name = task.get("name", "Unnamed Task")
    command_line = task.get("command_line", "")
    git_commit_message = task.get("git_commit_message", f"Automated update for {task_name}")

    git_repo_path = args.folder if args.folder is not None else task.get("git_repo_path")
    branch = args.branch if args.branch is not None else task.get("branch", "main")
    origin = args.origin if args.origin is not None else task.get("origin", "origin")

    log(f"\nTask Details: {task_name}", level='normal')
    log(f"  Git Repo Path: '{git_repo_path}' (from {'CLI' if args.folder is not None else 'config'})", level='normal')
    log(f"  Branch: '{branch}' (from {'CLI' if args.branch is not None else 'config/default'})", level='normal')
    log(f"  Origin: '{origin}' (from {'CLI' if args.origin is not None else 'config/default'})", level='normal')
    if command_line:
        log(f"  Pre-commit Command: '{command_line}'", level='normal')
    else:
        log("  No pre-commit command specified.", level='normal')
    log(f"  Git Commit Message: '{git_commit_message}'", level='normal')

    # --- Pre-requisite checks & Initialization ---
    if not git_repo_path:
        log(f"Error for '{task_name}': 'git_repo_path' is missing in config.json and not provided via --folder.", level='error')
        log(f"Task '{task_name}' aborted due to missing essential information.", level='error')
        sys.exit(1)

    git_dir_exists = os.path.exists(os.path.join(git_repo_path, '.git'))
    
    if not git_dir_exists:
        if args.initialize:
            log(f"Git repository not found at '{git_repo_path}'. Attempting to initialize...", level='step', task_name=task_name)
            if not initialize_repo(git_repo_path, origin_url=origin, task_name=task_name):
                log(f"Task '{task_name}' aborted: Git repository initialization failed.", level='error')
                sys.exit(1)
            log(f"Git repository initialized successfully.", level='success', task_name=task_name)
        else:
            log(f"Error for '{task_name}': Defined Git repository path '{git_repo_path}' is not a valid Git repository or does not exist.", level='error')
            log(f"To initialize it, use the --initialize flag.", level='error')
            log(f"Task '{task_name}' aborted as Git repository is not set up correctly.", level='error')
            sys.exit(1)
    else:
        log(f"Git repository found at '{git_repo_path}'.", level='normal', task_name=task_name)
        # If repo exists but initialize was specified, it's a no-op for init, but we proceed.

    # --- Checkout or Create Branch ---
    # The actual logging for this step is handled within checkout_or_create_branch in git_logic.py
    if not checkout_or_create_branch(git_repo_path, branch, origin, task_name):
        log(f"Task '{task_name}' aborted: Failed to checkout or create branch '{branch}'.", level='error')
        sys.exit(1)
    # No duplicate success log here, as git_logic handles it.


    # --- Initial Git Pull ---
    log("Performing initial Git Pull", level='step', task_name=task_name)
    if pull_updates(git_repo_path, branch, task_name):
        log(f"Initial Git Pull completed successfully.", level='success', task_name=task_name)
    else:
        log(f"Task '{task_name}' aborted: Initial Git Pull failed.", level='error')
        sys.exit(1)


    # --- Execute Command Line ---
    log("Executing command_line", level='step', task_name=task_name)
    if command_line:
        if execute_command(command_line, task_name, cwd=git_repo_path):
            log(f"Command execution completed successfully.", level='success', task_name=task_name)
        else:
            log(f"Task '{task_name}' aborted: Command execution failed.", level='error')
            sys.exit(1)
    else:
        log("No command_line to execute.", level='normal', task_name=task_name)


    # --- Check for Changes & Commit ---
    log("Checking for changes in Git Repository", level='step', task_name=task_name)
    changes_found = diff_changes(git_repo_path, task_name) # diff_changes logs its own details
    
    if changes_found is None:
        log(f"Task '{task_name}' aborted: Failed to check for Git differences.", level='error')
        sys.exit(1)
    elif changes_found:
        log("Changes detected. Performing Git Add and Commit", level='step', task_name=task_name)
        # add_commit_changes handles its own logging of add/commit steps
        if add_commit_changes(git_repo_path, git_commit_message, ".", task_name):
            log(f"Git Add and Commit completed successfully.", level='success', task_name=task_name)
            commit_successful = True
        else:
            log(f"Task '{task_name}' aborted: Git Add/Commit failed.", level='error')
            sys.exit(1)
    else:
        log("No changes detected. Skipping Git Add and Commit.", level='normal', task_name=task_name)
        commit_successful = False


    # --- Git Push ---
    if commit_successful:
        log("Commits made. Performing Git Push", level='step', task_name=task_name)
        if push_updates(git_repo_path, branch, origin, task_name):
            log(f"Git Push completed successfully.", level='success', task_name=task_name)
        else:
            log(f"Task '{task_name}' completed with warnings: Git Push failed.", level='error')
    else:
        log("No new commits to push. Skipping Git Push.", level='normal', task_name=task_name)


    # --- Final Git Pull (Post-push sync) ---
    log("Performing final Git Pull (post-push sync)", level='step', task_name=task_name)
    if pull_updates(git_repo_path, branch, task_name):
        log(f"Final Git Pull completed successfully.", level='success', task_name=task_name)
    else:
        log(f"Task '{task_name}' completed with warnings: Final Git Pull failed.", level='error')


    log(f"Task '{task_name}' completed successfully!", level='success', task_name=task_name)