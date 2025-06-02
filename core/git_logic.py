
import subprocess
import os
from core.logger import log
from core.messages import MESSAGES

def _run_git_command(repo_path, command_args, task_name=""):
    """Helper to run git commands."""
    cmd = ['git'] + command_args
    log(MESSAGES["git_executing_command"].format(' '.join(command_args), repo_path), level='debug', task_name=task_name)
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            check=False, # We check returncode manually
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                log(MESSAGES["git_stdout"].format(line), level='debug', task_name=task_name)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                log(MESSAGES["git_stderr"].format(line), level='debug', task_name=task_name)

        if result.returncode != 0:
            log(MESSAGES["git_command_failed"].format(result.returncode), level='error', task_name=task_name)
            return result.stdout.strip(), False # Return stdout even on failure for debugging
        return result.stdout.strip(), True
    except FileNotFoundError:
        log(MESSAGES["git_error_not_found"].format(cmd[0]), level='error', task_name=task_name)
        return None, False
    except Exception as e:
        log(MESSAGES["git_error_unexpected"].format(e), level='error', task_name=task_name)
        return None, False

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

    log(MESSAGES["git_initializing_repo"], level='normal', task_name=task_name)
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            log(MESSAGES["git_created_dir_for_repo"].format(path), level='info', task_name=task_name)
        except OSError as e:
            log(MESSAGES["git_error_creating_dir"].format(path, e), level='error', task_name=task_name)
            return False

    _, success = _run_git_command(path, ['init'], task_name=task_name)
    if not success:
        log(MESSAGES["git_init_failed"].format(path), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_init_successful"].format(path), level='success', task_name=task_name)
    return True

def add_remote(repo_path, origin_url, task_name=""):
    """Adds or updates the 'origin' remote."""
    if not origin_url:
        log("No origin URL provided to add.", level='debug', task_name=task_name)
        return True # Not an error if origin is empty

    log(MESSAGES["git_adding_remote_origin"].format(origin_url), level='normal', task_name=task_name)
    # Check if origin already exists
    stdout, success = _run_git_command(repo_path, ['remote'], task_name=task_name)
    if not success:
        return False

    if 'origin' in stdout.splitlines():
        # Update existing origin
        _, success = _run_git_command(repo_path, ['remote', 'set-url', 'origin', origin_url], task_name=task_name)
        if not success:
            log(MESSAGES["git_add_remote_failed"].format(origin_url), level='error', task_name=task_name)
            return False
    else:
        # Add new origin
        _, success = _run_git_command(repo_path, ['remote', 'add', 'origin', origin_url], task_name=task_name)
        if not success:
            log(MESSAGES["git_add_remote_failed"].format(origin_url), level='error', task_name=task_name)
            return False
    log(MESSAGES["git_add_remote_successful"].format(origin_url), level='success', task_name=task_name)
    return True

def checkout_or_create_branch(repo_path, branch_name, origin_url="", task_name=""):
    """Checks out an existing branch or creates a new one, handling remote tracking."""
    log(MESSAGES["git_checkout_or_create_branch_step"].format(branch_name), level='step', task_name=task_name)

    # Use 'git rev-parse --verify' to reliably check if a local branch exists
    local_branch_exists = False
    _, success_check = _run_git_command(repo_path, ['rev-parse', '--verify', branch_name], task_name=task_name)
    if success_check:
        local_branch_exists = True

    if local_branch_exists:
        log(MESSAGES["git_branch_found_local"].format(branch_name), level='info', task_name=task_name)
        log(MESSAGES["git_attempting_checkout_existing"].format(branch_name), level='normal', task_name=task_name)
        _, success = _run_git_command(repo_path, ['checkout', branch_name], task_name=task_name)
        if not success:
            log(MESSAGES["git_checkout_failed"].format(branch_name), level='error', task_name=task_name)
            return False
        log(MESSAGES["git_checkout_successful"].format(branch_name), level='success', task_name=task_name)
        return True
    else:
        log(MESSAGES["git_branch_not_found_local"].format(branch_name), level='info', task_name=task_name)
        
        # Check if branch exists on remote
        remote_branch_exists = False
        if origin_url:
            stdout_remote, success_remote = _run_git_command(repo_path, ['ls-remote', '--heads', 'origin', branch_name], task_name=task_name)
            if success_remote and f'refs/heads/{branch_name}' in stdout_remote:
                remote_branch_exists = True
                log(MESSAGES["git_branch_found_remote"].format(branch_name, 'origin'), level='info', task_name=task_name)
                # Checkout remote branch as a new local tracking branch
                _, success = _run_git_command(repo_path, ['checkout', '--track', f'origin/{branch_name}'], task_name=task_name)
                if not success:
                    log(MESSAGES["git_checkout_failed"].format(branch_name), level='error', task_name=task_name)
                    return False
                log(MESSAGES["git_checkout_successful"].format(branch_name), level='success', task_name=task_name)
                return True
            elif not success_remote:
                log(MESSAGES["git_branch_not_found_remote"].format(branch_name, 'origin'), level='warning', task_name=task_name)
        
        # If not found locally or remotely, create new branch
        log(MESSAGES["git_creating_new_branch"].format(branch_name), level='normal', task_name=task_name)
        _, success = _run_git_command(repo_path, ['checkout', '-b', branch_name], task_name=task_name)
        if not success:
            log(MESSAGES["git_create_branch_failed"].format(branch_name), level='error', task_name=task_name)
            return False
        
        log(MESSAGES["git_create_checkout_successful"].format(branch_name), level='success', task_name=task_name)

        # Set upstream for the new branch immediately
        if origin_url:
            log(MESSAGES["git_pushing_new_branch"].format(branch_name, 'origin', branch_name), level='normal', task_name=task_name)
            _, success = _run_git_command(repo_path, ['push', '-u', 'origin', branch_name], task_name=task_name)
            if not success:
                log(MESSAGES["git_push_new_branch_failed_warning"].format(branch_name, 'origin', branch_name), level='warning', task_name=task_name)
                # Do not return False here, as the branch was created locally
        
    log(MESSAGES["git_branch_op_completed"].format(branch_name), level='debug', task_name=task_name)
    return True

def pull_updates(repo_path, branch, task_name=""):
    """Pulls latest updates for the specified branch."""
    log(MESSAGES["git_pulling_updates"].format(branch), level='normal', task_name=task_name)
    _, success = _run_git_command(repo_path, ['pull', 'origin', branch], task_name=task_name)
    if not success:
        log(MESSAGES["git_pull_failed"].format(branch), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_pull_successful"].format(branch), level='success', task_name=task_name)
    return True

def check_for_changes(repo_path, task_name=""):
    """Checks if there are any uncommitted changes or untracked files."""
    log(MESSAGES["git_checking_status"], level='debug', task_name=task_name)
    stdout, success = _run_git_command(repo_path, ['status', '--porcelain'], task_name=task_name)
    if not success:
        log(MESSAGES["git_error_status_check"], level='error', task_name=task_name)
        return False, True # False for changes, True for error
    
    if stdout:
        log(MESSAGES["git_changes_detected"], level='debug', task_name=task_name)
        return True, False # True for changes, False for no error
    else:
        log(MESSAGES["git_no_changes_detected"], level='debug', task_name=task_name)
        return False, False # False for changes, False for no error

def git_add_commit(repo_path, commit_message, task_name=""):
    """Stages all changes and commits them."""
    log(MESSAGES["git_staging_changes"].format('.'), level='normal', task_name=task_name)
    _, success = _run_git_command(repo_path, ['add', '.'], task_name=task_name)
    if not success:
        log(MESSAGES["git_add_failed"], level='error', task_name=task_name)
        return False
    
    log(MESSAGES["git_committing_changes"].format(commit_message), level='normal', task_name=task_name)
    _, success = _run_git_command(repo_path, ['commit', '-m', commit_message], task_name=task_name)
    if not success:
        log(MESSAGES["git_commit_failed"], level='error', task_name=task_name)
        return False
    
    log(MESSAGES["git_add_commit_successful"], level='success', task_name=task_name)
    return True

def git_push(repo_path, branch, task_name=""):
    """Pushes changes to the remote repository."""
    log(MESSAGES["git_pushing_changes"].format('origin', branch), level='normal', task_name=task_name)
    _, success = _run_git_command(repo_path, ['push', 'origin', branch], task_name=task_name)
    if not success:
        log(MESSAGES["git_push_failed"].format('origin', branch), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_push_successful"], level='success', task_name=task_name)
    return True

def stash_local_changes(repo_path, task_name=""):
    """Stashes local changes including untracked files."""
    log(MESSAGES["git_changes_found_stashing"], level='normal', task_name=task_name)
    # Using --include-untracked to stash new files too
    stdout, success = _run_git_command(repo_path, ['stash', 'save', '--include-untracked', 'git-automation-temp-stash'], task_name=task_name)
    # Check stdout for "No local changes to save" instead of stderr for success check
    if not success and "No local changes to save" not in stdout:
        # A true failure if success is False and it's not just "no changes"
        log(MESSAGES["git_stash_failed"].format("Failed to save stash."), level='error', task_name=task_name)
        return False
    
    if "No local changes to save" in stdout:
        log(MESSAGES["git_no_changes_to_stash"], level='info', task_name=task_name)
        return True # Still considered successful as no action was needed
    
    log(MESSAGES["git_stash_successful"], level='success', task_name=task_name)
    return True

def pop_stashed_changes(repo_path, task_name=""):
    """Applies stashed changes back."""
    log(MESSAGES["git_stash_pop_applying"], level='normal', task_name=task_name)
    # Check if there's anything in the stash using 'git stash list'
    stdout_list, success_list = _run_git_command(repo_path, ['stash', 'list'], task_name=task_name)
    if not success_list or not stdout_list:
        log(MESSAGES["git_stash_pop_no_stash"], level='info', task_name=task_name)
        return True # Nothing to pop, so successful

    stdout, success = _run_git_command(repo_path, ['stash', 'pop'], task_name=task_name)
    if not success:
        if "Merge conflict" in stdout or "could not apply all your changes" in stdout:
            log(MESSAGES["git_stash_pop_failed_conflict"], level='error', task_name=task_name)
        else:
            log(MESSAGES["git_stash_pop_failed_general"].format(stdout.strip()), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_stash_pop_successful"], level='success', task_name=task_name)
    return True