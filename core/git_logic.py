# core/git_logic.py

import subprocess
import os
from core.logger import log
from core.messages import MESSAGES

def _run_git_command(command_parts, cwd, task_name=""):
    """
    Internal helper to run git commands and log their output.
    Returns (True, stdout, stderr) on success, (False, "", stderr) on failure.
    """
    command_str = " ".join(["git"] + command_parts)
    # Changed level from 'verbose' to 'debug' here
    log(MESSAGES["git_executing_command"].format(command_str, cwd), level='debug', task_name=task_name)
    
    try:
        process = subprocess.run(
            ["git"] + command_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False, # We handle return code manually
            env=os.environ
        )

        if process.stdout:
            # Changed level from 'verbose' to 'debug' here
            log(MESSAGES["git_stdout"].format(process.stdout.strip()), level='debug', task_name=task_name)
        if process.stderr:
            # Changed level from 'verbose' to 'debug' here
            log(MESSAGES["git_stderr"].format(process.stderr.strip()), level='debug', task_name=task_name)

        if process.returncode == 0:
            return True, process.stdout.strip(), process.stderr.strip()
        else:
            log(MESSAGES["git_command_failed"].format(process.returncode), level='error', task_name=task_name)
            return False, process.stdout.strip(), process.stderr.strip()

    except FileNotFoundError:
        log(MESSAGES["git_error_not_found"].format(command_parts[0]), level='error', task_name=task_name)
        return False, "", "Git command not found."
    except Exception as e:
        log(MESSAGES["git_error_unexpected"].format(e), level='error', task_name=task_name)
        return False, "", str(e)

def is_git_repo(path, task_name=""):
    """Checks if the given path is a valid Git repository."""
    # A simple check: does a .git directory exist?
    git_path = os.path.join(path, '.git')
    is_repo = os.path.isdir(git_path)
    if not is_repo:
        log(f"DEBUG: Not a Git repository: {path}", level='debug', task_name=task_name)
    return is_repo

def init_repo(path, task_name=""):
    """Initializes a new Git repository at the given path."""
    if is_git_repo(path, task_name):
        log(MESSAGES["git_repo_already_exists"].format(path), level='info', task_name=task_name)
        return True # Already a repo, consider it successful initialization

    log(MESSAGES["git_initializing_repo"].format(path), level='normal', task_name=task_name)
    
    # Ensure the directory exists
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            log(MESSAGES["git_created_dir_for_repo"].format(path), level='normal', task_name=task_name)
        except OSError as e:
            log(MESSAGES["git_error_creating_dir"].format(path, e), level='error', task_name=task_name)
            return False

    success, _, _ = _run_git_command(["init"], cwd=path, task_name=task_name)
    if not success:
        log(MESSAGES["git_init_failed"].format(path), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_init_successful"].format(path), level='success', task_name=task_name)
    return True

def add_remote(path, origin_url, task_name=""):
    """Adds a remote origin to the repository."""
    log(MESSAGES["git_adding_remote_origin"].format(origin_url), level='normal', task_name=task_name)
    success, _, stderr = _run_git_command(["remote", "add", "origin", origin_url], cwd=path, task_name=task_name)
    if not success and "remote origin already exists" not in stderr:
        log(MESSAGES["git_add_remote_failed"].format(origin_url), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_add_remote_successful"].format(origin_url), level='success', task_name=task_name)
    return True

def checkout_or_create_branch(path, branch_name, origin_url=None, task_name=""):
    """Checks out an existing branch or creates a new one if it doesn't exist locally/remotely."""
    log(MESSAGES["git_checkout_or_create_branch_step"].format(branch_name), level='normal', task_name=task_name)

    # Check if branch exists locally
    success_local, stdout_local, _ = _run_git_command(["branch", "--list", branch_name], cwd=path, task_name=task_name)
    if success_local and stdout_local.strip():
        log(MESSAGES["git_branch_found_local"].format(branch_name), level='info', task_name=task_name)
        log(MESSAGES["git_attempting_checkout_existing"].format(branch_name), level='normal', task_name=task_name)
        success_checkout, _, _ = _run_git_command(["checkout", branch_name], cwd=path, task_name=task_name)
        if success_checkout:
            log(MESSAGES["git_checkout_successful"].format(branch_name), level='success', task_name=task_name)
            return True
        else:
            log(MESSAGES["git_checkout_failed"].format(branch_name), level='error', task_name=task_name)
            return False

    log(MESSAGES["git_branch_not_found_local"].format(branch_name), level='info', task_name=task_name)

    # If not local, try to fetch from remote to see if it exists there
    if origin_url:
        _run_git_command(["fetch", "origin"], cwd=path, task_name=task_name) # Fetch latest
        success_remote, stdout_remote, _ = _run_git_command(["branch", "--remotes", "--list", f"origin/{branch_name}"], cwd=path, task_name=task_name)
        if success_remote and stdout_remote.strip():
            log(MESSAGES["git_branch_found_remote"].format(branch_name, "origin"), level='info', task_name=task_name)
            # Checkout tracking branch
            success_checkout, _, _ = _run_git_command(["checkout", "-t", f"origin/{branch_name}"], cwd=path, task_name=task_name)
            if success_checkout:
                log(MESSAGES["git_checkout_successful"].format(branch_name), level='success', task_name=task_name)
                return True
            else:
                log(MESSAGES["git_checkout_failed"].format(branch_name), level='error', task_name=task_name)
                return False
        else:
            log(MESSAGES["git_branch_not_found_remote"].format(branch_name, "origin"), level='info', task_name=task_name)
    
    # If not local and not on remote, create new branch
    log(MESSAGES["git_creating_new_branch"].format(branch_name), level='normal', task_name=task_name)
    success_create, _, _ = _run_git_command(["checkout", "-b", branch_name], cwd=path, task_name=task_name)
    if not success_create:
        log(MESSAGES["git_create_branch_failed"].format(branch_name), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_create_checkout_successful"].format(branch_name), level='success', task_name=task_name)

    # If origin was provided, push new branch to set upstream
    if origin_url:
        log(MESSAGES["git_pushing_new_branch"].format(branch_name, "origin", branch_name), level='normal', task_name=task_name)
        success_push, _, _ = _run_git_command(["push", "-u", "origin", branch_name], cwd=path, task_name=task_name)
        if not success_push:
            log(MESSAGES["git_push_new_branch_failed_warning"].format(branch_name, "origin", branch_name), level='warning', task_name=task_name)
            # Do not return False here, as the branch is created locally
    
    log(MESSAGES["git_branch_op_completed"].format(branch_name), level='debug', task_name=task_name)
    return True


def pull_updates(path, remote="origin", branch="main", task_name=""):
    """Pulls latest updates from the remote repository."""
    log(MESSAGES["git_pulling_updates"].format(branch), level='normal', task_name=task_name)
    success, _, _ = _run_git_command(["pull", remote, branch], cwd=path, task_name=task_name)
    if not success:
        log(MESSAGES["git_pull_failed"].format(branch), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_pull_successful"].format(branch), level='success', task_name=task_name)
    return True

def check_for_changes(path, task_name=""):
    """
    Checks if there are any pending changes (staged or unstaged) in the repository.
    Returns (True, False) if changes found, (False, False) if no changes, (False, True) on error.
    """
    log(MESSAGES["git_checking_status"], level='normal', task_name=task_name)
    # Changed level from 'verbose' to 'debug' here
    success, stdout, _ = _run_git_command(["status", "--porcelain"], cwd=path, task_name=task_name)
    if not success:
        log(MESSAGES["git_error_status_check"], level='error', task_name=task_name)
        return False, True # Return False for changes, True for error

    if stdout.strip():
        log(MESSAGES["git_changes_detected"], level='info', task_name=task_name)
        return True, False
    else:
        log(MESSAGES["git_no_changes_detected"], level='info', task_name=task_name)
        return False, False

def git_add_commit(path, commit_message, task_name=""):
    """Stages all changes and commits them."""
    log(MESSAGES["git_staging_changes"].format("."), level='normal', task_name=task_name)
    success, _, _ = _run_git_command(["add", "."], cwd=path, task_name=task_name)
    if not success:
        log(MESSAGES["git_add_failed"], level='error', task_name=task_name)
        return False

    log(MESSAGES["git_committing_changes"].format(commit_message), level='normal', task_name=task_name)
    success, _, _ = _run_git_command(["commit", "-m", commit_message], cwd=path, task_name=task_name)
    if not success:
        log(MESSAGES["git_commit_failed"], level='error', task_name=task_name)
        return False
    
    log(MESSAGES["git_add_commit_successful"], level='success', task_name=task_name)
    return True

def git_push(path, remote="origin", branch="main", task_name=""):
    """Pushes committed changes to the remote repository."""
    log(MESSAGES["git_pushing_changes"].format(remote, branch), level='normal', task_name=task_name)
    success, _, _ = _run_git_command(["push", remote, branch], cwd=path, task_name=task_name)
    if not success:
        log(MESSAGES["git_push_failed"].format(remote, branch), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_push_successful"], level='success', task_name=task_name)
    return True

def stash_local_changes(path, task_name=""):
    """Stashes local changes."""
    log(MESSAGES["git_changes_found_stashing"], level='normal', task_name=task_name)
    # Changed level from 'verbose' to 'debug' for internal stash command execution log
    success, stdout, stderr = _run_git_command(["stash", "save", "--include-untracked", "Automated stash"], cwd=path, task_name=task_name)
    if not success and "No local changes to save" not in stdout and "No local changes to save" not in stderr:
        log(MESSAGES["git_stash_failed"].format(stderr), level='error', task_name=task_name)
        return False
    
    if "No local changes to save" in stdout or "No local changes to save" in stderr:
        log(MESSAGES["git_no_changes_to_stash"], level='normal', task_name=task_name)
    else:
        log(MESSAGES["git_stash_successful"], level='success', task_name=task_name)
    return True

def pop_stashed_changes(path, task_name=""):
    """Applies the most recent stash."""
    log(MESSAGES["git_stash_pop_applying"], level='normal', task_name=task_name)
    # Changed level from 'verbose' to 'debug' for internal stash command execution log
    success, stdout, stderr = _run_git_command(["stash", "pop"], cwd=path, task_name=task_name)

    if not success:
        if "No stash entries found" in stdout or "No stash entries found" in stderr:
            log(MESSAGES["git_stash_pop_no_stash"], level='normal', task_name=task_name)
            return True # No stash to pop, consider successful
        elif "Merge conflict" in stdout or "Merge conflict" in stderr:
            log(MESSAGES["git_stash_pop_failed_conflict"], level='error', task_name=task_name)
            return False
        else:
            log(MESSAGES["git_stash_pop_failed_general"].format(stderr), level='error', task_name=task_name)
            return False
    
    log(MESSAGES["git_stash_pop_successful"], level='success', task_name=task_name)
    return True