# core/git_logic.py

import subprocess
import os
from datetime import datetime
from core.logger import log
from core.messages import MESSAGES

def _execute_git_command(command_parts, cwd, task_name, log_stdout_stderr=True):
    """
    Executes a Git command and logs its output.
    Returns: (stdout: str, success: bool)
    Special handling for 'git diff' where exit code 1 means differences found (not an error).
    """
    cmd_str = "git " + " ".join(command_parts)
    log(MESSAGES["git_executing_command"].format(cmd_str, cwd), level='debug', task_name=task_name)

    is_diff_command = command_parts[0] == 'diff'
    is_revert_command = command_parts[0] == 'revert' # NEW: Identify revert commands

    try:
        result = subprocess.run(
            ['git'] + command_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False # Do not raise CalledProcessError automatically; we handle return codes manually
        )

        if log_stdout_stderr and result.stdout:
            log(MESSAGES["git_stdout"].format(result.stdout.strip()), level='debug', task_name=task_name)
        if log_stdout_stderr and result.stderr:
            log(MESSAGES["git_stderr"].format(result.stderr.strip()), level='debug', task_name=task_name)

        # Special handling for git diff: exit code 1 means differences found (success for our purpose)
        if is_diff_command and result.returncode == 1:
            log(MESSAGES["git_command_failed"].format(result.returncode), level='debug', task_name=task_name) # Log as debug for diff
            return result.stdout.strip(), True # Treat as success
        
        # NEW: Special handling for git revert: exit code 1 means conflicts (not a fatal error, but needs attention)
        if is_revert_command and result.returncode == 1:
            log(MESSAGES["git_command_failed"].format(result.returncode), level='warning', task_name=task_name)
            # Signal conflict by returning false, and let calling function interpret
            return result.stdout.strip() + "\n" + result.stderr.strip(), False 
        
        # For all other commands, or if diff/revert command had a fatal error (exit code > 1)
        if result.returncode != 0:
            log(MESSAGES["git_command_failed"].format(result.returncode), level='error', task_name=task_name)
            return result.stdout.strip() + "\n" + result.stderr.strip(), False # Indicate failure (concat stdout/stderr for error message)
        
        return result.stdout.strip(), True # Success (exit code 0)

    except FileNotFoundError:
        log(MESSAGES["git_error_not_found"], level='error', task_name=task_name)
        return "", False
    except Exception as e:
        log(MESSAGES["git_error_unexpected"].format(e), level='error', task_name=task_name)
        return "", False

def initialize_repo(repo_path, origin_url=None, task_name=""):
    """Initializes a new Git repository and adds an origin."""
    log(MESSAGES["git_initializing_repo"].format(repo_path), level='step', task_name=task_name)
    
    # Check if directory exists, create if not
    if not os.path.exists(repo_path):
        log(MESSAGES["git_created_dir_for_repo"].format(repo_path), level='normal', task_name=task_name)
        try:
            os.makedirs(repo_path, exist_ok=True)
        except Exception as e:
            log(MESSAGES["git_error_creating_dir"].format(repo_path, e), level='error', task_name=task_name)
            return False

    # Check if already a git repo
    if os.path.exists(os.path.join(repo_path, '.git')):
        log(MESSAGES["git_repo_already_exists"].format(repo_path), level='normal', task_name=task_name)
        return True # Already initialized, consider it a success

    # Initialize
    _, success = _execute_git_command(['init'], cwd=repo_path, task_name=task_name)
    if not success:
        log(MESSAGES["git_init_failed"].format(repo_path), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_init_successful"].format(repo_path), level='success', task_name=task_name)

    # Add origin if specified
    if origin_url:
        log(MESSAGES["git_adding_remote_origin"].format(origin_url), level='step', task_name=task_name)
        _, success = _execute_git_command(['remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name)
        if not success:
            log(MESSAGES["git_add_remote_failed"].format(origin_url), level='error', task_name=task_name)
            # Do not return False here, as the repo is initialized; just warn about origin
        else:
            log(MESSAGES["git_add_remote_successful"].format(origin_url), level='success', task_name=task_name)
    return True

def checkout_or_create_branch(repo_path, branch_name, origin_name="origin", task_name=""):
    """
    Checks out an existing branch or creates a new one if it doesn't exist,
    and sets its upstream if pushed.
    """
    log(MESSAGES["git_checkout_or_create_branch_step"].format(branch_name), level='step', task_name=task_name)

    # 1. Fetch remote to ensure we have up-to-date branch info
    log(MESSAGES["git_fetching_remote"].format(origin_name), level='debug', task_name=task_name)
    _, fetch_success = _execute_git_command(['fetch', origin_name], cwd=repo_path, task_name=task_name)
    if not fetch_success:
        log(MESSAGES["git_fetch_failed_warning"].format(origin_name), level='warning', task_name=task_name)
        # Continue anyway, local branch operations might still work

    # 2. Check if local branch exists
    stdout_local, _ = _execute_git_command(['branch', '--list', branch_name], cwd=repo_path, task_name=task_name, log_stdout_stderr=False)
    local_branch_exists = (branch_name in stdout_local)

    # 3. Check if remote branch exists
    stdout_remote, _ = _execute_git_command(['ls-remote', '--heads', origin_name, branch_name], cwd=repo_path, task_name=task_name, log_stdout_stderr=False)
    remote_branch_exists = bool(stdout_remote.strip())

    if local_branch_exists:
        log(MESSAGES["git_branch_found_local"].format(branch_name), level='normal', task_name=task_name)
        log(MESSAGES["git_attempting_checkout_existing"].format(branch_name), level='normal', task_name=task_name)
        _, success = _execute_git_command(['checkout', branch_name], cwd=repo_path, task_name=task_name)
        if not success:
            log(MESSAGES["git_checkout_failed"].format(branch_name), level='error', task_name=task_name)
            return False
        log(MESSAGES["git_checkout_successful"].format(branch_name), level='success', task_name=task_name)
    elif remote_branch_exists:
        log(MESSAGES["git_branch_found_remote"].format(branch_name, origin_name), level='normal', task_name=task_name)
        log(MESSAGES["git_creating_new_branch"].format(branch_name), level='normal', task_name=task_name)
        # Create local branch and set upstream to remote
        _, success = _execute_git_command(['checkout', '-b', branch_name, f'{origin_name}/{branch_name}'], cwd=repo_path, task_name=task_name)
        if not success:
            log(MESSAGES["git_create_branch_failed"].format(branch_name), level='error', task_name=task_name)
            return False
        log(MESSAGES["git_create_checkout_successful"].format(branch_name), level='success', task_name=task_name)
    else:
        log(MESSAGES["git_branch_not_found_local"].format(branch_name), level='normal', task_name=task_name)
        log(MESSAGES["git_branch_not_found_remote"].format(branch_name, origin_name), level='normal', task_name=task_name)
        log(MESSAGES["git_creating_new_branch"].format(branch_name), level='normal', task_name=task_name)
        # Create a brand new local branch (will need to push -u later)
        _, success = _execute_git_command(['checkout', '-b', branch_name], cwd=repo_path, task_name=task_name)
        if not success:
            log(MESSAGES["git_create_branch_failed"].format(branch_name), level='error', task_name=task_name)
            return False
        log(MESSAGES["git_create_checkout_successful"].format(branch_name), level='success', task_name=task_name)
        # Attempt to set upstream immediately for new local-only branches
        log(MESSAGES["git_pushing_new_branch"].format(branch_name, origin_name), level='normal', task_name=task_name)
        _, push_success = _execute_git_command(['push', '-u', origin_name, branch_name], cwd=repo_path, task_name=task_name)
        if not push_success:
            log(MESSAGES["git_push_new_branch_failed_warning"].format(branch_name, origin_name), level='warning', task_name=task_name)
            # Not a fatal error, just a warning that upstream wasn't set

    log(MESSAGES["git_branch_op_completed"].format(branch_name), level='step', task_name=task_name)
    return True


def _check_for_unstaged_changes(repo_path, task_name):
    """
    Checks if there are any uncommitted changes (staged or unstaged, excluding untracked files with '??').
    Returns True if changes are found, False if no changes.
    """
    # Use --porcelain=v1 to get a stable format, only showing changes to tracked files.
    # We are interested in any status other than '??' (untracked).
    stdout, success = _execute_git_command(['status', '--porcelain=v1'], cwd=repo_path, task_name=task_name, log_stdout_stderr=False)
    if not success:
        log(MESSAGES["git_error_status_check"], level='error', task_name=task_name)
        return False # Indicate error during check

    # Filter out untracked files ('??') from the status output
    # This leaves 'M', 'A', 'D', 'R', 'C' etc. (staged or unstaged changes to tracked files)
    lines_with_changes = [line for line in stdout.strip().splitlines() if not line.startswith('??')]
    
    if lines_with_changes:
        log(MESSAGES["git_local_changes_detected_pull_blocked"], level='normal', task_name=task_name)
        # Log the actual changes at debug level
        for line in lines_with_changes:
            log(f"  Detected change: {line}", level='debug', task_name=task_name)
        return True
    else:
        log(MESSAGES["git_skipping_stash_no_changes"], level='normal', task_name=task_name)
        return False

def stash_local_changes(repo_path, task_name):
    """Stashes local changes (including untracked files) before a pull."""
    log(MESSAGES["git_auto_stashing_changes"], level='step', task_name=task_name)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stash_message = f"gitb_auto_stash_{timestamp}" # Use timestamp for uniqueness
    stdout, success = _execute_git_command(['stash', 'push', '--include-untracked', '-m', stash_message], cwd=repo_path, task_name=task_name)
    
    if not success:
        log(MESSAGES["git_stash_failed"], level='error', task_name=task_name)
        return False
    
    # Check if a stash was actually created (e.g., "No local changes to save" means it wasn't)
    if "No local changes to save" in stdout: # Git prints this if nothing was stashed
        log(MESSAGES["git_skipping_stash_no_changes"], level='normal', task_name=task_name)
        return False # Indicate no stash was performed because nothing was there
    
    log(MESSAGES["git_stash_successful"], level='success', task_name=task_name)
    return True

def pop_stashed_changes(repo_path, task_name):
    """Attempts to apply stashed changes back after a pull."""
    log(MESSAGES["git_stash_pop_applying"], level='step', task_name=task_name)

    # Check if there are any stashes first
    stdout_list, success_list = _execute_git_command(['stash', 'list'], cwd=repo_path, task_name=task_name, log_stdout_stderr=False)
    if not success_list or not stdout_list.strip():
        log(MESSAGES["git_stash_pop_no_stash"], level='normal', task_name=task_name)
        return True # Nothing to pop, so consider it successful

    # Attempt to pop the most recent stash
    stdout_pop, success_pop = _execute_git_command(['stash', 'pop'], cwd=repo_path, task_name=task_name)
    
    if not success_pop:
        # Check for conflict indicators in stdout or stderr
        if "Merge conflict" in stdout_pop or "conflict" in stdout_pop or \
           "could not apply all your changes" in stdout_pop:
            log(MESSAGES["git_stash_pop_failed_conflict"], level='error', task_name=task_name)
        else:
            log(MESSAGES["git_stash_failed"].format(stdout_pop.strip()), level='error', task_name=task_name)
        return False # Stash pop failed
    
    log(MESSAGES["git_stash_pop_successful"], level='success', task_name=task_name)
    return True

def pull_updates(repo_path, branch, task_name=""):
    """Performs a Git pull operation."""
    log(MESSAGES["git_pulling_updates"].format(branch), level='normal', task_name=task_name)
    _, success = _execute_git_command(['pull', 'origin', branch], cwd=repo_path, task_name=task_name)
    if not success:
        log(MESSAGES["git_pull_failed"].format(branch), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_pull_successful"], level='success', task_name=task_name)
    return True

def diff_changes(repo_path, task_name=""):
    """
    Checks for all changes (staged, unstaged, untracked) in the repository
    and returns a boolean indicating if any changes are found.
    This is for `diff_changes` (for `git status` check) not `_check_for_unstaged_changes`.
    """
    log(MESSAGES["git_checking_status"], level='normal', task_name=task_name)
    stdout, success = _execute_git_command(['status', '--porcelain'], cwd=repo_path, task_name=task_name)
    
    if not success:
        log(MESSAGES["git_error_status_check"], level='error', task_name=task_name)
        return None # Indicate error
    
    if stdout.strip():
        log(MESSAGES["git_changes_detected"], level='normal', task_name=task_name)
        return True
    else:
        log(MESSAGES["git_no_changes_detected"], level='normal', task_name=task_name)
        return False

def add_commit_changes(repo_path, commit_message_base, files_to_add=".", task_name=""):
    """
    Stages changes and commits them.
    Appends a timestamp to the commit message.
    """
    log(MESSAGES["git_staging_changes"].format(files_to_add), level='normal', task_name=task_name)
    _, success = _execute_git_command(['add', files_to_add], cwd=repo_path, task_name=task_name)
    if not success:
        log(MESSAGES["git_add_failed"], level='error', task_name=task_name)
        return False

    # Append timestamp to the commit message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_commit_message = f"{commit_message_base} [Auto@{timestamp}]"

    log(MESSAGES["git_committing_changes"].format(final_commit_message), level='normal', task_name=task_name)
    _, success = _execute_git_command(['commit', '-m', final_commit_message], cwd=repo_path, task_name=task_name)
    
    # git commit returns 1 if "nothing to commit" which is fine for us (no new commit made)
    # The _execute_git_command handles this by returning True if it's "nothing to commit"
    if not success:
        log(MESSAGES["git_commit_failed"], level='error', task_name=task_name)
        return False
    
    log(MESSAGES["git_add_commit_successful"], level='success', task_name=task_name)
    return True # True means changes were added and a commit was attempted (might be "nothing to commit")


def push_updates(repo_path, branch, origin="origin", task_name=""):
    """Performs a Git push operation."""
    log(MESSAGES["git_pushing_changes"].format(branch, origin), level='normal', task_name=task_name)
    _, success = _execute_git_command(['push', origin, branch], cwd=repo_path, task_name=task_name)
    if not success:
        log(MESSAGES["git_push_failed"].format(branch, origin), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_push_successful"], level='success', task_name=task_name)
    return True


def get_last_commits(repo_path, num_commits=5, task_name=""):
    """
    Retrieves and displays the last N commits from the specified repository.
    Returns True on success, False on error.
    """
    log(MESSAGES["git_showing_last_commits"].format(num_commits, repo_path), level='step', task_name=task_name)
    
    # Check if it's a Git repository
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        log(MESSAGES["workflow_error_repo_not_valid"].format(task_name, repo_path), level='error')
        return False

    # git log --pretty=format:"%h - %an, %ar : %s" -n N
    # %h: commit hash (abbreviated)
    # %an: author name
    # %ar: author date, relative
    # %s: subject (commit message title)
    cmd_parts = ['log', f'--pretty=format:%h - %an, %ar : %s', f'-n{num_commits}']
    stdout, success = _execute_git_command(cmd_parts, cwd=repo_path, task_name=task_name)

    if not success:
        log(MESSAGES["git_no_commits_found"].format(repo_path), level='error', task_name=task_name)
        return False
    
    if not stdout.strip():
        log(MESSAGES["git_no_commits_found"].format(repo_path), level='normal', task_name=task_name)
        return True # No commits, but command succeeded
        
    print("\n" + stdout + "\n") # Print raw git log output for readability
    return True

def revert_commit(repo_path, commit_hash, task_name=""):
    """
    Reverts a specific commit in the given repository.
    Returns True on success, False on error (including conflicts).
    """
    log(MESSAGES["git_revert_start"].format(commit_hash, repo_path), level='step', task_name=task_name)

    # Check if it's a Git repository
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        log(MESSAGES["workflow_error_repo_not_valid"].format(task_name, repo_path), level='error')
        return False

    # Check if the commit hash exists (optional but good for user feedback)
    stdout_check, success_check = _execute_git_command(['rev-parse', '--verify', commit_hash + '^{commit}'], cwd=repo_path, task_name=task_name, log_stdout_stderr=False)
    if not success_check:
        log(MESSAGES["git_revert_no_commit_found"].format(commit_hash, repo_path), level='error', task_name=task_name)
        return False

    # Execute git revert --no-edit (to prevent opening an editor)
    # The user has already confirmed, so we assume they want the default revert message.
    # We might want to make this configurable later.
    stdout_revert, success_revert = _execute_git_command(['revert', '--no-edit', commit_hash], cwd=repo_path, task_name=task_name)

    if success_revert:
        log(MESSAGES["git_revert_success"].format(commit_hash), level='success', task_name=task_name)
        return True
    else:
        # Check for merge conflict indicators in the stderr/stdout from _execute_git_command
        # _execute_git_command already concatenates stdout/stderr on failure
        if "conflict" in stdout_revert.lower() or "merge" in stdout_revert.lower():
            log(MESSAGES["git_revert_conflict"].format(commit_hash), level='error', task_name=task_name)
        else:
            log(MESSAGES["git_revert_failed"].format(commit_hash, "See logs above for details."), level='error', task_name=task_name)
        return False