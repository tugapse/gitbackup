import subprocess
import os
from datetime import datetime
from core.logger import log

def run_git_command(repo_path, command_args, task_name, capture_output=False):
    """
    Helper function to run a git command.
    Logs command execution and output at 'normal' level, errors at 'error' level.
    """
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
            log(f"Git STDOUT:\n{process.stdout.strip()}", level='normal', task_name=task_name)
        if process.stderr:
            log(f"Git STDERR:\n{process.stderr.strip()}", level='normal', task_name=task_name)

        if process.returncode != 0:
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
    log(f"Pulling updates for branch '{branch}'...", level='normal', task_name=task_name)
    result = run_git_command(repo_path, ["pull", "origin", branch], task_name)
    if result is None:
        log(f"Git Pull failed for branch '{branch}'.", level='error', task_name=task_name)
        return False
    log(f"Git Pull successful.", level='normal', task_name=task_name)
    return True

def diff_changes(repo_path, task_name):
    """
    Checks for any changes (modified, untracked, deleted, etc.) in the Git repository.
    Logs at 'normal' level for non-critical information.
    """
    log(f"Checking for pending changes using 'git status --porcelain'...", level='normal', task_name=task_name)
    output = run_git_command(repo_path, ["status", "--porcelain"], task_name, capture_output=True)

    if output is None:
        log(f"Error during Git status check.", level='error', task_name=task_name)
        return None
    elif output:
        log(f"Changes detected.", level='normal', task_name=task_name)
        return True
    else:
        log(f"No changes detected.", level='normal', task_name=task_name)
        return False

def add_commit_changes(repo_path, commit_message, files_to_add, task_name):
    """
    Stages specified files and commits them to the repository.
    Appends a timestamp to the commit message.
    Logs at 'normal' level for non-critical information.
    """
    timestamp = datetime.now().strftime("%m%d%H%M%S") # MMDDHHMMSS
    final_commit_message = f"{commit_message} [{timestamp}]"

    log(f"Staging changes ('{files_to_add}')...", level='normal', task_name=task_name)
    add_result = run_git_command(repo_path, ["add", files_to_add], task_name)
    if add_result is None:
        log(f"Git Add failed.", level='error', task_name=task_name)
        return False

    log(f"Committing changes with message: '{final_commit_message}'...", level='normal', task_name=task_name)
    commit_result = run_git_command(repo_path, ["commit", "-m", final_commit_message], task_name)
    if commit_result is None:
        log(f"Git Commit failed.", level='error', task_name=task_name)
        return False

    log(f"Git Add and Commit successful.", level='normal', task_name=task_name)
    return True

def push_updates(repo_path, branch, origin, task_name):
    """
    Pushes committed changes to the specified remote origin and branch.
    Logs at 'normal' level for non-critical information.
    """
    log(f"Pushing changes to '{origin}/{branch}'...", level='normal', task_name=task_name)
    push_result = run_git_command(repo_path, ["push", origin, branch], task_name)
    if push_result is None:
        log(f"Git Push failed to '{origin}/{branch}'.", level='error', task_name=task_name)
        return False
    log(f"Git Push successful.", level='normal', task_name=task_name)
    return True

def initialize_repo(repo_path, origin_url=None, task_name=None):
    """
    Initializes a Git repository in the given path.
    If origin_url is provided, it also adds the remote origin.
    """
    git_dir = os.path.join(repo_path, '.git')
    if os.path.exists(git_dir):
        log(f"Git repository already exists at '{repo_path}'. Skipping initialization.", level='normal', task_name=task_name)
        return True # Already initialized, so consider it a success for this step

    log(f"Initializing new Git repository at '{repo_path}'...", level='step', task_name=task_name)
    # Ensure the directory exists before initializing
    if not os.path.exists(repo_path):
        try:
            os.makedirs(repo_path, exist_ok=True)
            log(f"Created directory for repository: '{repo_path}'", level='normal', task_name=task_name)
        except Exception as e:
            log(f"Error creating repository directory '{repo_path}': {e}", level='error', task_name=task_name)
            return False

    init_result = run_git_command(repo_path, ["init"], task_name)
    if init_result is None:
        log(f"Git repository initialization failed at '{repo_path}'.", level='error', task_name=task_name)
        return False
    log(f"Git repository initialized successfully at '{repo_path}'.", level='normal', task_name=task_name)

    if origin_url:
        log(f"Adding remote origin '{origin_url}'...", level='normal', task_name=task_name)
        add_remote_result = run_git_command(repo_path, ["remote", "add", "origin", origin_url], task_name)
        if add_remote_result is None:
            log(f"Failed to add remote origin '{origin_url}'.", level='error', task_name=task_name)
            return False
        log(f"Remote origin '{origin_url}' added successfully.", level='normal', task_name=task_name)
    
    return True

# NEW FUNCTION: checkout_or_create_branch
def checkout_or_create_branch(repo_path, branch_name, origin_name, task_name):
    """
    Checks if a branch exists on the remote, checks it out if it does,
    otherwise creates it locally.
    """
    log(f"Checking out or creating branch '{branch_name}'...", level='step', task_name=task_name)

    # First, try to fetch to ensure remote branches are up-to-date
    log(f"Fetching from remote '{origin_name}' to update branch list...", level='normal', task_name=task_name)
    fetch_result = run_git_command(repo_path, ["fetch", origin_name], task_name)
    if fetch_result is None:
        log(f"Failed to fetch from remote '{origin_name}'. This might affect branch detection.", level='warning', task_name=task_name)
        # Continue as branch might exist locally or be created
    
    # Check if branch exists remotely
    # git ls-remote --heads <origin> <branch_name>
    remote_branch_check = run_git_command(repo_path, ["ls-remote", "--heads", origin_name, branch_name], task_name, capture_output=True)
    
    branch_exists_remotely = False
    if remote_branch_check is not None and remote_branch_check.strip():
        branch_exists_remotely = True
        log(f"Branch '{branch_name}' found on remote '{origin_name}'.", level='normal', task_name=task_name)
    else:
        log(f"Branch '{branch_name}' not found on remote '{origin_name}'.", level='normal', task_name=task_name)

    # Check if branch exists locally
    local_branch_check = run_git_command(repo_path, ["branch", "--list", branch_name], task_name, capture_output=True)
    branch_exists_locally = False
    if local_branch_check is not None and local_branch_check.strip():
        # The output of `git branch --list <name>` includes a '*' if it's the current branch
        # or just the name if it exists but is not current. Either way, it means it exists.
        branch_exists_locally = True
        log(f"Branch '{branch_name}' found locally.", level='normal', task_name=task_name)
    else:
        log(f"Branch '{branch_name}' not found locally.", level='normal', task_name=task_name)

    if branch_exists_remotely or branch_exists_locally:
        # If it exists remotely or locally, try to check it out
        log(f"Attempting to checkout existing branch '{branch_name}'...", level='normal', task_name=task_name)
        checkout_result = run_git_command(repo_path, ["checkout", branch_name], task_name)
        if checkout_result is None:
            log(f"Failed to checkout branch '{branch_name}'.", level='error', task_name=task_name)
            return False
        log(f"Successfully checked out branch '{branch_name}'.", level='normal', task_name=task_name)
        
    else:
        # If it doesn't exist remotely or locally, create it
        log(f"Creating new local branch '{branch_name}'...", level='normal', task_name=task_name)
        create_result = run_git_command(repo_path, ["checkout", "-b", branch_name], task_name)
        if create_result is None:
            log(f"Failed to create new branch '{branch_name}'.", level='error', task_name=task_name)
            return False
        log(f"Successfully created and checked out new branch '{branch_name}'.", level='normal', task_name=task_name)

        # After creating a new branch, push it to set upstream
        if origin_name:
            log(f"Pushing new branch '{branch_name}' to '{origin_name}' to set upstream...", level='normal', task_name=task_name)
            push_new_branch_result = run_git_command(repo_path, ["push", "-u", origin_name, branch_name], task_name)
            if push_new_branch_result is None:
                log(f"Failed to push new branch '{branch_name}' to '{origin_name}'.", level='warning', task_name=task_name)
                # It's a warning because the branch is created locally, but the remote setup failed.
                # The workflow can still proceed but subsequent pushes might require manual upstream setup.

    log(f"Branch operation for '{branch_name}' completed.", level='success', task_name=task_name)
    return True