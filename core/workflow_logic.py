# core/workflow_logic.py

import subprocess
import os
import shutil
from types import SimpleNamespace

from core.logger import log
from core.messages import MESSAGES

def _is_git_repo(folder_path):
    """Checks if the given folder is a Git repository."""
    return os.path.isdir(os.path.join(folder_path, '.git'))

def _check_for_changes(repo_path, task_name):
    """Checks if there are any uncommitted changes or untracked files."""
    stdout, success = _execute_git_command(['status', '--porcelain'], cwd=repo_path, task_name=task_name, log_level='debug')
    if not success:
        log(MESSAGES["git_error_status_check"], level='error', task_name=task_name)
        return False, True # False for changes, True for error
    
    if stdout.strip(): # If stdout is not empty, there are changes
        log(MESSAGES["git_changes_detected_status_check"], level='debug', task_name=task_name)
        return True, False # True for changes, False for no error
    else:
        log(MESSAGES["git_no_changes_detected_status_check"], level='debug', task_name=task_name)
        return False, False # False for changes, False for no error

def _stash_local_changes(repo_path, task_name):
    """Stashes local changes including untracked files."""
    log(MESSAGES["git_changes_found_stashing"], level='normal', task_name=task_name)
    # Using --include-untracked to stash new files too
    # Git stash returns 0 on success, even if nothing is stashed (prints "No local changes to save")
    # Our _execute_git_command uses check=True, so it will raise CalledProcessError if there's an actual error.
    stdout_raw, success = _execute_git_command(['stash', 'push', '--include-untracked', '-m', 'git-automation-temp-stash'], cwd=repo_path, task_name=task_name)

    if not success:
        # If _execute_git_command returned False, it's a real failure
        log(MESSAGES["git_stash_failed"].format("Failed to save stash."), level='error', task_name=task_name)
        return False
    
    # If success is True, it means stash command ran successfully (either stashed or nothing to stash)
    log(MESSAGES["git_stash_successful"], level='success', task_name=task_name)
    return True

def _pop_stashed_changes(repo_path, task_name):
    """Applies stashed changes back."""
    log(MESSAGES["git_stash_pop_applying"], level='normal', task_name=task_name)
    
    # Check if there's anything in the stash using 'git stash list'
    stdout_list, success_list = _execute_git_command(['stash', 'list'], cwd=repo_path, task_name=task_name, log_level='debug')
    if not success_list or not stdout_list.strip(): # .strip() handles empty string effectively
        log(MESSAGES["git_stash_pop_no_stash"], level='info', task_name=task_name)
        return True # Nothing to pop, so successful

    stdout_raw, success = _execute_git_command(['stash', 'pop'], cwd=repo_path, task_name=task_name)
    if not success:
        # Check for conflict messages in the raw stdout/stderr to provide specific feedback
        if "Merge conflict" in stdout_raw or "could not apply all your changes" in stdout_raw or \
           "Auto-merging" in stdout_raw: # Auto-merging often precedes "could not apply"
            log(MESSAGES["git_stash_pop_failed_conflict"], level='error', task_name=task_name)
        else:
            log(MESSAGES["git_stash_pop_failed_general"].format(stdout_raw.strip()), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_stash_pop_successful"], level='success', task_name=task_name)
    return True


def _execute_git_command(command_parts, cwd, task_name, log_level='info'):
    """Executes a Git command and logs its output."""
    cmd_str = "git " + " ".join(command_parts) # Include 'git' in the displayed command string
    log(MESSAGES["git_executing_command"].format(cmd_str), level='debug', task_name=task_name)
    try:
        result = subprocess.run(
            ['git'] + command_parts, # Actual command parts array for subprocess
            cwd=cwd,
            check=True, # Will raise CalledProcessError on non-zero exit codes
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                log(f"  OUT: {line}", level='debug', task_name=task_name)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                log(f"  ERR: {line}", level='debug', task_name=task_name) # Git stderr often contains info, so debug
        return result.stdout.strip(), True # Return stdout and success status
    except subprocess.CalledProcessError as e:
        output_combined = (e.stdout or "") + (e.stderr or "")
        
        # Special handling for git commit returning 1 on no changes
        if command_parts[0] == 'commit' and (
           "nothing to commit, working tree clean" in output_combined or
           "no changes added to commit" in output_combined or
           "nada a memorizar, árvore-trabalho limpa" in output_combined):
            log(MESSAGES["git_no_changes_to_commit"], level='info', task_name=task_name)
            # Log stdout/stderr as debug for context
            if e.stdout:
                for line in e.stdout.strip().splitlines():
                    log(f"  OUT: {line}", level='debug', task_name=task_name)
            if e.stderr:
                for line in e.stderr.strip().splitlines():
                    log(f"  ERR: {line}", level='debug', task_name=task_name)
            return "", True # Return True for success because it's a valid non-op
        
        # General error logging for any other Git command failure
        log(MESSAGES["git_command_failed"].format(cmd_str, e.returncode), level='error', task_name=task_name)
        if e.stdout:
            for line in e.stdout.strip().splitlines():
                log(f"  OUT: {line}", level='error', task_name=task_name)
        if e.stderr:
            for line in e.stderr.strip().splitlines():
                log(f"  ERR: {line}", level='error', task_name=task_name)
        return e.stdout.strip(), False # Return stdout and False for actual failure
    except FileNotFoundError:
        log(MESSAGES["git_not_found"], level='error', task_name=task_name)
        return None, False
    except Exception as e:
        log(MESSAGES["git_command_exception"].format(cmd_str, e), level='error', task_name=task_name)
        return None, False

def run_task_workflow(args: SimpleNamespace, task: SimpleNamespace, config_file_path: str):
    """
    Executes the full Git automation workflow for a given task.
    """
    task_name = task.name

    log(MESSAGES["workflow_start"].format(task_name), level='info', task_name=task_name)
    
    repo_path = task.folder
    branch = task.branch
    origin_url = task.origin

    # Ensure repository directory exists
    if not os.path.exists(repo_path):
        log(MESSAGES["workflow_creating_folder"].format(repo_path), level='step', task_name=task_name)
        try:
            os.makedirs(repo_path, exist_ok=True)
            log(MESSAGES["workflow_folder_created"], level='success', task_name=task_name)
        except Exception as e:
            log(MESSAGES["workflow_folder_creation_failed"].format(repo_path, e), level='error', task_name=task_name)
            return False

    # Check if it's a Git repository and initialize if needed
    if not _is_git_repo(repo_path):
        if args.initialize:
            log(MESSAGES["git_initializing_repo"].format(repo_path), level='step', task_name=task_name)
            if not _execute_git_command(['init'], cwd=repo_path, task_name=task_name)[1]: # [1] for success status
                return False
            if origin_url:
                log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
                if not _execute_git_command(['remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name)[1]:
                    return False
            log(MESSAGES["git_repo_initialized"], level='success', task_name=task_name)
        else:
            log(MESSAGES["git_not_repo_and_not_init"].format(repo_path), level='error', task_name=task_name)
            return False
    elif origin_url:
        # Check if origin already exists and has the correct URL
        stdout_remotes, success_remotes = _execute_git_command(['remote', '-v'], cwd=repo_path, task_name=task_name, log_level='debug')
        if not success_remotes: # Failed to list remotes
            return False
        
        origin_exists = False
        for line in stdout_remotes.splitlines():
            if line.startswith('origin') and origin_url in line:
                origin_exists = True
                break
        
        if not origin_exists:
            log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
            if not _execute_git_command(['remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name)[1]:
                return False

    # Checkout or switch to the specified branch
    log(MESSAGES["git_checking_out_branch"].format(branch), level='step', task_name=task_name)
    
    # --- UPDATED LOGIC FOR LOCAL BRANCH EXISTENCE CHECK ---
    # Use 'git rev-parse --verify' to reliably check if a local branch exists
    _, local_branch_exists = _execute_git_command(['rev-parse', '--verify', branch], cwd=repo_path, task_name=task_name, log_level='debug')

    if local_branch_exists:
        log(MESSAGES["git_branch_found_local"].format(branch), level='info', task_name=task_name)
        if not _execute_git_command(['checkout', branch], cwd=repo_path, task_name=task_name)[1]:
            log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
            return False
    else:
        log(MESSAGES["git_branch_not_found_local"].format(branch), level='info', task_name=task_name)
        # Try checking out a remote tracking branch if it exists remotely
        stdout_remote_branches, success_remote_branches = _execute_git_command(['ls-remote', '--heads', 'origin', branch], cwd=repo_path, task_name=task_name, log_level='debug')
        
        remote_branch_exists = success_remote_branches and f'refs/heads/{branch}' in stdout_remote_branches

        if remote_branch_exists:
            log(MESSAGES["git_branch_found_remote"].format(branch, 'origin'), level='info', task_name=task_name)
            if not _execute_git_command(['checkout', '--track', f'origin/{branch}'], cwd=repo_path, task_name=task_name)[1]:
                log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
                return False
        else: # If not found locally or remotely, create new branch
            log(MESSAGES["git_branch_not_found_local_or_remote"].format(branch), level='info', task_name=task_name)
            if not _execute_git_command(['checkout', '-b', branch], cwd=repo_path, task_name=task_name)[1]:
                log(MESSAGES["git_branch_creation_failed"].format(branch), level='error', task_name=task_name)
                return False
            # Push new branch to set upstream
            if origin_url:
                log(MESSAGES["git_pushing_new_branch"].format(branch, 'origin', branch), level='normal', task_name=task_name)
                if not _execute_git_command(['push', '-u', 'origin', branch], cwd=repo_path, task_name=task_name)[1]:
                    log(MESSAGES["git_push_new_branch_failed_warning"].format(branch, 'origin', branch), level='warning', task_name=task_name)
                    # Don't return False, as local branch is created
    # --- END UPDATED LOGIC ---
        
    log(MESSAGES["git_on_branch"].format(branch), level='success', task_name=task_name)

    # Pull latest changes if configured
    if task.pull_before_command:
        log(MESSAGES["git_pulling_latest"], level='step', task_name=task_name)
        
        has_local_changes, check_error = _check_for_changes(repo_path, task_name)
        if check_error: return False
        
        stashed = False
        if has_local_changes:
            log(MESSAGES["workflow_local_changes_found_stashing"], level='info', task_name=task_name)
            if not _stash_local_changes(repo_path, task_name): return False
            stashed = True
        else:
            log(MESSAGES["workflow_no_local_changes_to_stash"], level='info', task_name=task_name)

        if not _execute_git_command(['pull', 'origin', branch], cwd=repo_path, task_name=task_name)[1]:
            log(MESSAGES["git_pull_failed"].format(branch), level='error', task_name=task_name)
            if stashed:
                log(MESSAGES["workflow_pull_failed_attempting_pop"], level='warning', task_name=task_name)
                _pop_stashed_changes(repo_path, task_name) # Attempt pop even if it fails
            return False
        log(MESSAGES["git_pull_successful"], level='success', task_name=task_name)

        if stashed:
            if not _pop_stashed_changes(repo_path, task_name):
                log(MESSAGES["workflow_pop_stash_failed_after_pull_warning"], level='warning', task_name=task_name)
                log(MESSAGES["workflow_manual_resolve_needed"], level='error', task_name=task_name)
                # Decide if a pop failure should stop the whole workflow. For now, warning.
    else:
        log(MESSAGES["workflow_pull_before_command_skipped"], level='info', task_name=task_name)

    # Execute pre-command
    if task.pre_command:
        if not _execute_command(task.pre_command, cwd=repo_path, task_name=task_name):
            log(MESSAGES["workflow_pre_command_failed"], level='error', task_name=task_name)
            return False
        log(MESSAGES["workflow_pre_command_successful"], level='success', task_name=task_name)

    # Add all changes and commit
    log(MESSAGES["git_adding_changes"], level='step', task_name=task_name)
    if not _execute_git_command(['add', '.'], cwd=repo_path, task_name=task_name)[1]:
        return False
    log(MESSAGES["git_changes_added"], level='success', task_name=task_name)

    log(MESSAGES["git_committing_changes"], level='step', task_name=task_name)
    # _execute_git_command handles "no changes to commit" gracefully as a success
    if not _execute_git_command(['commit', '-m', task.commit_message], cwd=repo_path, task_name=task_name)[1]:
        # If it returns False here, it means it was a genuine commit error
        return False
    # If it returned True, either a commit was made, or there were no changes
    # No explicit log for 'changes committed' here as _execute_git_command now logs "no changes"
        
    # Push changes if configured
    if task.push_after_command:
        log(MESSAGES["git_pushing_changes"].format(branch), level='step', task_name=task_name)
        if not _execute_git_command(['push', 'origin', branch], cwd=repo_path, task_name=task_name)[1]:
            return False
        log(MESSAGES["git_push_successful"], level='success', task_name=task_name)

    # Execute post-command
    if task.post_command:
        if not _execute_command(task.post_command, cwd=repo_path, task_name=task_name):
            log(MESSAGES["workflow_post_command_failed"], level='error', task_name=task_name)
            return False
        log(MESSAGES["workflow_post_command_successful"], level='success', task_name=task_name)

    log(MESSAGES["workflow_completed"].format(task_name), level='success', task_name=task_name)
    return True


def run_update_task_workflow(args: SimpleNamespace, task: SimpleNamespace, config_file_path: str):
    """
    Executes a simplified update workflow focused on pull/commit/push.
    This version implicitly skips pre_command and post_command.
    """
    task_name = task.name

    log(MESSAGES["update_workflow_start"].format(task_name), level='info', task_name=task_name)

    repo_path = task.folder
    branch = task.branch
    origin_url = task.origin

    # Ensure repository directory exists and is a Git repo
    if not os.path.exists(repo_path):
        log(MESSAGES["update_error_folder_not_found"].format(repo_path), level='error', task_name=task_name)
        return False
    if not _is_git_repo(repo_path):
        log(MESSAGES["update_error_not_git_repo"].format(repo_path), level='error', task_name=task_name)
        return False
    
    # Ensure origin is set if it was defined in config
    if origin_url:
        log(MESSAGES["git_checking_remote"].format(origin_url), level='debug', task_name=task_name)
        # Check if origin is already set or add it
        stdout_remotes, success_remotes = _execute_git_command(['remote', '-v'], cwd=repo_path, task_name=task_name, log_level='debug')
        if not success_remotes: # Failed to list remotes
            return False
        
        origin_exists = False
        for line in stdout_remotes.splitlines():
            if line.startswith('origin') and origin_url in line:
                origin_exists = True
                break
        
        if not origin_exists:
            log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
            if not _execute_git_command(['remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name)[1]:
                return False

    # Checkout or switch to the specified branch
    log(MESSAGES["git_checking_out_branch"].format(branch), level='step', task_name=task_name)
    
    # --- UPDATED LOGIC FOR LOCAL BRANCH EXISTENCE CHECK (again for update workflow) ---
    # Use 'git rev-parse --verify' to reliably check if a local branch exists
    _, local_branch_exists = _execute_git_command(['rev-parse', '--verify', branch], cwd=repo_path, task_name=task_name, log_level='debug')

    if local_branch_exists:
        log(MESSAGES["git_branch_found_local"].format(branch), level='info', task_name=task_name)
        if not _execute_git_command(['checkout', branch], cwd=repo_path, task_name=task_name)[1]:
            log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
            return False
    else:
        log(MESSAGES["git_branch_not_found_local"].format(branch), level='info', task_name=task_name)
        # Try checking out a remote tracking branch if it exists remotely
        stdout_remote_branches, success_remote_branches = _execute_git_command(['ls-remote', '--heads', 'origin', branch], cwd=repo_path, task_name=task_name, log_level='debug')
        
        remote_branch_exists = success_remote_branches and f'refs/heads/{branch}' in stdout_remote_branches

        if remote_branch_exists:
            log(MESSAGES["git_branch_found_remote"].format(branch, 'origin'), level='info', task_name=task_name)
            if not _execute_git_command(['checkout', '--track', f'origin/{branch}'], cwd=repo_path, task_name=task_name)[1]:
                log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
                return False
        else: # If not found locally or remotely, create new branch
            log(MESSAGES["git_branch_not_found_local_or_remote"].format(branch), level='info', task_name=task_name)
            if not _execute_git_command(['checkout', '-b', branch], cwd=repo_path, task_name=task_name)[1]:
                log(MESSAGES["git_branch_creation_failed"].format(branch), level='error', task_name=task_name)
                return False
            # Push new branch to set upstream
            if origin_url:
                log(MESSAGES["git_pushing_new_branch"].format(branch, 'origin', branch), level='normal', task_name=task_name)
                if not _execute_git_command(['push', '-u', 'origin', branch], cwd=repo_path, task_name=task_name)[1]:
                    log(MESSAGES["git_push_new_branch_failed_warning"].format(branch, 'origin', branch), level='warning', task_name=task_name)
                    # Don't return False, as local branch is created
    # --- END UPDATED LOGIC (for update workflow) ---
        
    log(MESSAGES["git_on_branch"].format(branch), level='success', task_name=task_name)

    # --- START STASH/PULL/POP LOGIC FOR UPDATE WORKFLOW ---
    log(MESSAGES["git_pulling_latest"], level='step', task_name=task_name)
    
    has_local_changes, check_error = _check_for_changes(repo_path, task_name)
    if check_error: return False
    
    stashed = False
    if has_local_changes:
        log(MESSAGES["workflow_local_changes_found_stashing"], level='info', task_name=task_name)
        if not _stash_local_changes(repo_path, task_name): return False
        stashed = True
    else:
        log(MESSAGES["workflow_no_local_changes_to_stash"], level='info', task_name=task_name)

    if not _execute_git_command(['pull', 'origin', branch], cwd=repo_path, task_name=task_name)[1]:
        log(MESSAGES["git_pull_failed"].format(branch), level='error', task_name=task_name)
        if stashed:
            log(MESSAGES["workflow_pull_failed_attempting_pop"], level='warning', task_name=task_name)
            _pop_stashed_changes(repo_path, task_name) # Attempt pop even if it fails
        return False
    log(MESSAGES["git_pull_successful"], level='success', task_name=task_name)

    if stashed:
        if not _pop_stashed_changes(repo_path, task_name):
            log(MESSAGES["workflow_pop_stash_failed_after_pull_warning"], level='warning', task_name=task_name)
            log(MESSAGES["workflow_manual_resolve_needed"], level='error', task_name=task_name)
            # Decide if a pop failure should stop the whole workflow. For now, warning.
    # --- END STASH/PULL/POP LOGIC FOR UPDATE WORKFLOW ---

    # Pre-command is explicitly skipped in update workflow
    log(MESSAGES["update_skipping_pre_post_commands"], level='info', task_name=task_name)

    # Add all changes and commit
    log(MESSAGES["git_adding_changes"], level='step', task_name=task_name)
    if not _execute_git_command(['add', '.'], cwd=repo_path, task_name=task_name)[1]:
        return False
    log(MESSAGES["git_changes_added"], level='success', task_name=task_name)

    log(MESSAGES["git_committing_changes"], level='step', task_name=task_name)
    # _execute_git_command handles "no changes to commit" gracefully as a success
    if not _execute_git_command(['commit', '-m', task.commit_message], cwd=repo_path, task_name=task_name)[1]:
        # If it returns False here, it means it was a genuine commit error
        return False
    
    # Push changes if configured
    if task.push_after_command:
        log(MESSAGES["git_pushing_changes"].format(branch), level='step', task_name=task_name)
        if not _execute_git_command(['push', 'origin', branch], cwd=repo_path, task_name=task_name)[1]:
            return False
        log(MESSAGES["git_push_successful"], level='success', task_name=task_name)

    log(MESSAGES["update_workflow_completed"].format(task_name), level='success', task_name=task_name)
    return True