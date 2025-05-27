import subprocess
import os

def run_git_command(repo_path, command_args, task_name, capture_output=False):
    """
    Helper function to run a git command.
    Captures and prints stdout/stderr for better debugging.
    Returns True for success, None for failure.
    If capture_output is True, returns stdout string on success.
    """
    full_command = ["git"] + command_args
    print(f"  [{task_name}] Executing Git command: {' '.join(full_command)} in '{repo_path}'")
    try:
        process = subprocess.run(
            full_command,
            cwd=repo_path,
            capture_output=True, # Always capture to be able to print errors/output
            text=True,           # Decode stdout/stderr as text
            check=False          # Do not raise CalledProcessError automatically; we handle returncode
        )

        # Print standard output if any
        if process.stdout:
            print(f"  [{task_name}] Git STDOUT:\n{process.stdout.strip()}")

        # Print standard error if any
        if process.stderr:
            print(f"  [{task_name}] Git STDERR:\n{process.stderr.strip()}")

        if process.returncode != 0:
            print(f"  [{task_name}] Git command FAILED with exit code {process.returncode}.")
            return None # Indicate failure

        return process.stdout.strip() if capture_output else True # Return output or simply True for success
    except FileNotFoundError:
        print(f"  [{task_name}] Error: 'git' command not found. Please ensure Git is installed and in your PATH.")
        return None
    except Exception as e:
        print(f"  [{task_name}] An unexpected error occurred while running Git command: {e}")
        return None

def pull_updates(repo_path, branch, task_name):
    """
    Performs a git pull on the specified branch and origin.
    """
    print(f"  [{task_name}] Pulling updates for branch '{branch}'...")
    # Assuming 'origin' is the default remote, but you can pass origin in command_args if needed
    result = run_git_command(repo_path, ["pull", "origin", branch], task_name)
    if result is None:
        print(f"  [{task_name}] Git Pull failed for branch '{branch}'.")
        return False
    print(f"  [{task_name}] Git Pull successful.")
    return True

def diff_changes(repo_path, task_name):
    """
    Checks for any changes (modified, untracked, deleted, etc.) in the Git repository.
    Returns True if changes are found, False if no changes, None on error.
    """
    print(f"  [{task_name}] Checking for pending changes using 'git status --porcelain'...")
    output = run_git_command(repo_path, ["status", "--porcelain"], task_name, capture_output=True)

    if output is None:
        print(f"  [{task_name}] Error during Git status check.")
        return None
    elif output:
        print(f"  [{task_name}] Changes detected.")
        return True
    else:
        print(f"  [{task_name}] No changes detected.")
        return False

def add_commit_changes(repo_path, commit_message, files_to_add, task_name):
    """
    Stages specified files and commits them to the repository.
    """
    print(f"  [{task_name}] Staging changes ('{files_to_add}')...")
    add_result = run_git_command(repo_path, ["add", files_to_add], task_name)
    if add_result is None:
        print(f"  [{task_name}] Git Add failed.")
        return False

    print(f"  [{task_name}] Committing changes with message: '{commit_message}'...")
    commit_result = run_git_command(repo_path, ["commit", "-m", commit_message], task_name)
    if commit_result is None:
        print(f"  [{task_name}] Git Commit failed.")
        return False

    print(f"  [{task_name}] Git Add and Commit successful.")
    return True

# New function to push changes
def push_updates(repo_path, branch, origin, task_name):
    """
    Pushes committed changes to the specified remote origin and branch.
    """
    print(f"  [{task_name}] Pushing changes to '{origin}/{branch}'...")
    push_result = run_git_command(repo_path, ["push", origin, branch], task_name)
    if push_result is None:
        print(f"  [{task_name}] Git Push failed to '{origin}/{branch}'.")
        return False
    print(f"  [{task_name}] Git Push successful.")
    return True