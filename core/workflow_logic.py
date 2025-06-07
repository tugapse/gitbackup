# core/workflow_logic.py

import subprocess
import os
import shutil
from types import SimpleNamespace
from datetime import datetime

from core.logger import log
from core.messages import MESSAGES

def _is_git_repo(folder_path):
    """Checks if the given folder is a Git repository."""
    return os.path.isdir(os.path.join(folder_path, '.git'))

def _check_for_changes(repo_path, task_name):
    """Checks if there are any uncommitted changes or untracked files."""
    stdout, success, _ = _execute_git_command(['status', '--porcelain'], cwd=repo_path, task_name=task_name, log_level='debug')
    if not success:
        log(MESSAGES["git_error_status_check"], level='error', task_name=task_name)
        return False, True # False for changes, True for error (an actual error in status check)
    
    if stdout.strip(): # If stdout is not empty, there are changes
        log(MESSAGES["git_changes_detected_status_check"], level='debug', task_name=task_name)
        # --- NEW: Log the specific changes detected at debug level ---
        for line in stdout.strip().splitlines():
            log(f"  Detected change: {line}", level='debug', task_name=task_name)
        # --- END NEW ---
        return True, False # True for changes, False for no error
    else:
        log(MESSAGES["git_no_changes_detected_status_check"], level='debug', task_name=task_name)
        return False, False # False for changes, False for no error

def _stash_local_changes(repo_path, task_name, custom_message=None):
    """
    Stashes local changes including untracked files.
    This function should only log its own execution and outcome, not decision messages.
    """
    stash_message = custom_message if custom_message else "git-automation-temp-stash"
    log(f"Stashing local changes with message: '{stash_message}'...", level='debug', task_name=task_name) # Debug log for internal action
    
    stdout_raw, success, _ = _execute_git_command(['stash', 'push', '--include-untracked', '-m', stash_message], cwd=repo_path, task_name=task_name)

    if not success:
        log(MESSAGES["git_stash_failed"].format("Failed to save stash."), level='error', task_name=task_name)
        return False
    
    # Only log success/failure here for the operation itself
    # The higher-level workflow logs the decision to stash
    log(MESSAGES["git_stash_successful"], level='success', task_name=task_name)
    return True

def _pop_stashed_changes(repo_path, task_name):
    """Applies stashed changes back."""
    log(MESSAGES["git_stash_pop_applying"], level='normal', task_name=task_name)
    
    # Check if there's anything in the stash using 'git stash list'
    stdout_list, success_list, _ = _execute_git_command(['stash', 'list'], cwd=repo_path, task_name=task_name, log_level='debug')
    if not success_list or not stdout_list.strip(): # .strip() handles empty string effectively
        log(MESSAGES["git_stash_pop_no_stash"], level='info', task_name=task_name)
        return True # Nothing to pop, so successful

    stdout_raw, success, _ = _execute_git_command(['stash', 'pop'], cwd=repo_path, task_name=task_name)
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
    """
    Executes a Git command and logs its output.
    Returns: (stdout: str, success: bool, commit_made: bool | None)
    commit_made is True if a commit was made, False if no changes to commit, None for other commands.
    """
    cmd_str = "git " + " ".join(command_parts) # Include 'git' in the displayed command string
    log(MESSAGES["git_executing_command"].format(cmd_str), level='debug', task_name=task_name)
    
    is_commit_command = (command_parts[0] == 'commit')

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

        if is_commit_command:
            # Check for specific "no changes" message in stdout
            if "nothing to commit, working tree clean" in result.stdout or \
               "no changes added to commit" in result.stdout or \
               "nada a memorizar, árvore-trabalho limpa" in result.stdout: # Handle Portuguese message as well
                log(MESSAGES["git_no_changes_to_commit"], level='info', task_name=task_name)
                return result.stdout.strip(), True, False # Success, but no commit made
            else:
                log(MESSAGES["git_changes_committed"], level='success', task_name=task_name) # Explicitly log commit success
                return result.stdout.strip(), True, True # Success, commit made
        
        return result.stdout.strip(), True, None # Return stdout, success, and None for non-commit commands
    except subprocess.CalledProcessError as e:
        output_combined = (e.stdout or "") + (e.stderr or "")
        
        # Special handling for git commit returning 1 on no changes (this case should ideally not happen if check=True is used carefully,
        # but kept for robustness if other errors like non-zero exit codes also contain "no changes")
        if is_commit_command and (
           "nothing to commit, working tree clean" in output_combined or
           "no changes added to commit" in output_combined or
           "nada a memorizar, árvore-trabalho limpa" in output_combined):
            log(MESSAGES["git_no_changes_to_commit"], level='info', task_name=task_name)
            if e.stdout:
                for line in e.stdout.strip().splitlines():
                    log(f"  OUT: {line}", level='debug', task_name=task_name)
            if e.stderr:
                for line in e.stderr.strip().splitlines():
                    log(f"  ERR: {line}", level='debug', task_name=task_name)
            return "", True, False # Treat as success (no commit made)
        
        # General error logging for any other Git command failure
        log(MESSAGES["git_command_failed"].format(cmd_str, e.returncode), level='error', task_name=task_name)
        if e.stdout:
            for line in e.stdout.strip().splitlines():
                log(f"  OUT: {line}", level='error', task_name=task_name)
        if e.stderr:
            for line in e.stderr.strip().splitlines():
                log(f"  ERR: {line}", level='error', task_name=task_name)
        return e.stdout.strip(), False, None # Return stdout, False for actual failure, None for commit_made
    except FileNotFoundError:
        log(MESSAGES["git_not_found"], level='error', task_name=task_name)
        return None, False, None
    except Exception as e:
        log(MESSAGES["git_command_exception"].format(cmd_str, e), level='error', task_name=task_name)
        return None, False, None

def _execute_command(command_line, cwd, task_name):
    """Executes a general shell command."""
    if not command_line:
        return True # No command to execute

    log(MESSAGES["cmd_executing"].format(command_line), level='step', task_name=task_name)
    try:
        # Using shell=True to allow complex commands and piping, but beware of shell injection
        result = subprocess.run(
            command_line,
            cwd=cwd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                log(f"  {line}", level='debug', task_name=task_name)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                log(f"  ERR: {line}", level='warning', task_name=task_name)
        log(MESSAGES["cmd_finished_successfully"], level='success', task_name=task_name)
        return True
    except subprocess.CalledProcessError as e:
        log(MESSAGES["cmd_failed_exit_code"].format(command_line, e.returncode), level='error', task_name=task_name)
        if e.stdout:
            for line in e.stdout.strip().splitlines():
                log(f"  OUT: {line}", level='error', task_name=task_name)
        if e.stderr:
            for line in e.stderr.strip().splitlines():
                log(f"  ERR: {line}", level='error', task_name=task_name)
        return False
    except FileNotFoundError:
        log(MESSAGES["cmd_not_found"].format(command_line.split()[0]), level='error', task_name=task_name)
        return False
    except Exception as e:
        log(MESSAGES["cmd_exception"].format(command_line, e), level='error', task_name=task_name)
        return False

# --- Helper for User Confirmation ---
def _prompt_for_confirmation(prompt_message, task_name=""):
    """
    Prompts the user for a 'yes' or 'no' confirmation.
    Returns True if 'yes', False otherwise.
    """
    log(prompt_message, level='warning', task_name=task_name)
    while True:
        try:
            response = input("  Type 'yes' to confirm, or anything else to cancel: ").strip().lower()
            if response == 'yes':
                return True
            else:
                log("Operation cancelled by user.", level='info', task_name=task_name)
                return False
        except KeyboardInterrupt:
            log("\nOperation cancelled by user (Ctrl+C).", level='info', task_name=task_name)
            return False

# --- Helper for Getting Remote Commits ---
def _get_remote_commits(repo_path, branch, task_name, num_commits=5):
    """
    Fetches the last N commits from the remote branch and returns them.
    Returns a list of dictionaries with (full_hash, short_hash, message, author, date) or None on failure.
    """
    log(MESSAGES["git_fetching_remote_commits"].format(branch), level='step', task_name=task_name)
    
    # First, ensure we have the latest remote history
    _, success, _ = _execute_git_command(['fetch', 'origin', branch], cwd=repo_path, task_name=task_name)
    if not success:
        log(MESSAGES["git_fetch_failed"].format(branch), level='error', task_name=task_name)
        return None

    # Use --pretty=format for controlled output: full_hash, short_hash, subject, author, date
    # %H: full hash, %h: abbreviated hash, %s: subject, %an: author name, %ad: author date
    # --date=format:'%Y-%m-%d %H:%M:%S': specifies date format
    log_format = "%H%x09%h%x09%s%x09%an%x09%ad"
    stdout, success, _ = _execute_git_command(['log', f'origin/{branch}', f'-n{num_commits}', f'--pretty=format:{log_format}', '--date=format:%Y-%m-%d %H:%M:%S'], cwd=repo_path, task_name=task_name)

    if not success:
        log(MESSAGES["git_log_failed"].format(f'origin/{branch}'), level='error', task_name=task_name)
        return None

    commits_data = []
    for line in stdout.splitlines():
        # Split by tab, expecting 5 parts
        parts = line.split('\t', 4) 
        if len(parts) == 5:
            full_hash, short_hash, message, author, date = parts
            commits_data.append({'full_hash': full_hash, 'short_hash': short_hash, 'message': message, 'author': author, 'date': date})
    
    return commits_data

# --- Workflow for Showing Last Commits ---
def run_show_last_commits_workflow(args: SimpleNamespace, task: SimpleNamespace):
    """
    Displays the last N commits from the remote branch of the specified task.
    """
    task_name = task.name
    
    # --- FIX: Prioritize command-line overrides ---
    repo_path = args.folder if args.folder else task.folder
    branch = args.branch if args.branch else task.branch
    origin_url = args.origin if args.origin else task.origin # For consistency
    # --- END FIX ---

    log(MESSAGES["show_last_commits_start"].format(task_name, branch), level='info', task_name=task_name)

    if not os.path.exists(repo_path) or not _is_git_repo(repo_path):
        log(MESSAGES["git_not_repo_or_not_found"].format(repo_path), level='error', task_name=task_name)
        return

    # Ensure remote origin is set if specified
    if origin_url: # Use origin_url from combined args/task
        stdout_remotes, success_remotes, _ = _execute_git_command(['remote', '-v'], cwd=repo_path, task_name=task_name, log_level='debug')
        if not success_remotes or origin_url not in stdout_remotes:
            log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
            _, success_add_remote, _ = _execute_git_command(['remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name)
            if not success_add_remote:
                return

    commits = _get_remote_commits(repo_path, branch, task_name)
    if commits is None:
        return # Error already logged

    if not commits:
        log(MESSAGES["show_last_commits_no_commits"].format(branch), level='info', task_name=task_name)
        return

    log(MESSAGES["show_last_commits_listing"].format(branch), level='normal', task_name=task_name)
    for i, commit in enumerate(commits):
        log(f"{i + 1}. [{commit['short_hash']}] {commit['message']} ({commit['author']}, {commit['date']})", level='normal', task_name=task_name)

    log(MESSAGES["show_last_commits_completed"], level='success', task_name=task_name)


# --- Workflow for Interactive Revert (Cherry-Pick) with Automatic Stash ---
def run_revert_commit_workflow(args: SimpleNamespace, task: SimpleNamespace):
    """
    Allows interactive selection of a remote commit to cherry-pick.
    Automatically stashes local changes if detected before cherry-picking.
    """
    task_name = task.name
    
    # --- FIX: Prioritize command-line overrides ---
    repo_path = args.folder if args.folder else task.folder
    branch = args.branch if args.branch else task.branch
    origin_url = args.origin if args.origin else task.origin # For consistency
    # --- END FIX ---

    log(MESSAGES["revert_commit_start"].format(task_name), level='info', task_name=task_name)

    # Initial safety checks
    if not os.path.exists(repo_path) or not _is_git_repo(repo_path):
        log(MESSAGES["git_not_repo_or_not_found"].format(repo_path), level='error', task_name=task_name)
        return False

    # Ensure branch is checked out
    log(MESSAGES["git_checking_out_branch"].format(branch), level='step', task_name=task_name)
    _, local_branch_exists, _ = _execute_git_command(['rev-parse', '--verify', branch], cwd=repo_path, task_name=task_name, log_level='debug')
    if not local_branch_exists:
        log(MESSAGES["revert_error_branch_not_local"].format(branch), level='error', task_name=task_name)
        return False
    _, checkout_success, _ = _execute_git_command(['checkout', branch], cwd=repo_path, task_name=task_name)
    if not checkout_success:
        log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_on_branch"].format(branch), level='success', task_name=task_name)

    # --- START NEW STASH LOGIC FOR REVERT WORKFLOW ---
    has_local_changes, check_error = _check_for_changes(repo_path, task_name)
    if check_error: return False # Error checking changes

    stashed = False
    if has_local_changes:
        stash_message = f"git-automation-cherry-pick-temp-stash-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        log(MESSAGES["revert_auto_stashing_changes"].format(stash_message), level='warning', task_name=task_name)
        if not _stash_local_changes(repo_path, task_name, custom_message=stash_message):
            log(MESSAGES["revert_auto_stash_failed"], level='error', task_name=task_name)
            return False
        stashed = True
    else:
        log(MESSAGES["revert_no_local_changes_to_stash"], level='info', task_name=task_name)
    # --- END NEW STASH LOGIC FOR REVERT WORKFLOW ---

    # Fetch commits
    commits = _get_remote_commits(repo_path, branch, task_name, num_commits=5)
    if commits is None or not commits:
        log(MESSAGES["revert_no_commits_found"].format(branch), level='error', task_name=task_name)
        if stashed: # Attempt to pop stash even if no commits found for cherry-pick
            log(MESSAGES["revert_attempting_pop_after_no_commits"], level='warning', task_name=task_name)
            _pop_stashed_changes(repo_path, task_name)
        return False

    log(MESSAGES["revert_listing_commits"].format(branch), level='normal', task_name=task_name)
    for i, commit in enumerate(commits):
        log(f"{i + 1}. [{commit['short_hash']}] {commit['message']} ({commit['author']}, {commit['date']})", level='normal', task_name=task_name)

    selected_index = -1
    while not (0 <= selected_index <= len(commits)):
        try:
            user_input = input(MESSAGES["revert_prompt_selection"].format(len(commits))).strip()
            selected_index = int(user_input) - 1 # Adjust for 0-based indexing
            if selected_index == -1 and user_input == '0': # User wants to cancel
                log(MESSAGES["revert_cancelled"], level='info', task_name=task_name)
                if stashed:
                    log(MESSAGES["revert_attempting_pop_after_cancel"], level='warning', task_name=task_name)
                    _pop_stashed_changes(repo_path, task_name)
                return False
            if not (0 <= selected_index < len(commits)): # Check boundary again
                log(MESSAGES["revert_invalid_selection"], level='error', task_name=task_name)
                selected_index = -1 # Reset to loop again
        except ValueError:
            log(MESSAGES["revert_invalid_input"], level='error', task_name=task_name)
            selected_index = -1 # Reset to loop again
        except KeyboardInterrupt:
            log("\n" + MESSAGES["revert_cancelled"], level='info', task_name=task_name)
            if stashed:
                log(MESSAGES["revert_attempting_pop_after_cancel"], level='warning', task_name=task_name)
                _pop_stashed_changes(repo_path, task_name)
            return False

    selected_commit = commits[selected_index]

    log(MESSAGES["revert_confirm_cherry_pick"].format(selected_commit['short_hash'], selected_commit['message']), level='warning', task_name=task_name)
    if not _prompt_for_confirmation(MESSAGES["revert_confirm_proceed"], task_name=task_name):
        if stashed:
            log(MESSAGES["revert_attempting_pop_after_cancel"], level='warning', task_name=task_name)
            _pop_stashed_changes(repo_path, task_name)
        return False

    # Perform cherry-pick
    log(MESSAGES["revert_performing_cherry_pick"].format(selected_commit['short_hash']), level='step', task_name=task_name)
    _, cherry_pick_success, _ = _execute_git_command(['cherry-pick', selected_commit['full_hash'], '--no-edit'], cwd=repo_path, task_name=task_name)
    
    if not cherry_pick_success:
        log(MESSAGES["revert_cherry_pick_failed"].format(selected_commit['short_hash']), level='error', task_name=task_name)
        log(MESSAGES["revert_cherry_pick_conflict_instructions"], level='error', task_name=task_name)
        if stashed:
            log(MESSAGES["revert_attempting_pop_after_failure"], level='warning', task_name=task_name)
            _pop_stashed_changes(repo_path, task_name) # Attempt pop even on cherry-pick failure
        return False
    
    log(MESSAGES["revert_cherry_pick_successful"].format(selected_commit['short_hash']), level='success', task_name=task_name)

    # Automatic Push after successful cherry-pick
    if task.push_after_command:
        log(MESSAGES["git_pushing_changes"].format(branch), level='step', task_name=task_name)
        _, push_success, _ = _execute_git_command(['push', 'origin', branch], cwd=repo_path, task_name=task_name)
        if not push_success:
            log(MESSAGES["git_push_failed"].format(branch), level='error', task_name=task_name)
            if stashed: # Attempt pop even if push fails
                log(MESSAGES["revert_attempting_pop_after_failure"], level='warning', task_name=task_name)
                _pop_stashed_changes(repo_path, task_name)
            return False # Consider push failure after cherry-pick a workflow failure
        log(MESSAGES["git_push_successful"], level='success', task_name=task_name)
    else:
        log(MESSAGES["revert_push_skipped_after_cherry_pick"], level='info', task_name=task_name)

    # Pop stashed changes if they were stashed
    if stashed:
        if not _pop_stashed_changes(repo_path, task_name):
            log(MESSAGES["workflow_pop_stash_failed_after_pull_warning"], level='warning', task_name=task_name)
            log(MESSAGES["workflow_manual_resolve_needed"], level='error', task_name=task_name)
            # Do NOT return False here, as the cherry-pick itself was successful.
            # This is a post-operation warning for manual user intervention.

    log(MESSAGES["revert_completed"].format(task_name), level='success', task_name=task_name)
    return True


def run_task_workflow(args: SimpleNamespace, task: SimpleNamespace, config_file_path: str):
    """
    Executes the full Git automation workflow for a given task.
    """
    task_name = task.name

    log(MESSAGES["workflow_start"].format(task_name), level='info', task_name=task_name)
    
    # --- FIX: Prioritize command-line overrides ---
    repo_path = args.folder if args.folder else task.folder
    branch = args.branch if args.branch else task.branch
    origin_url = args.origin if args.origin else task.origin
    # --- END FIX ---

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
            _, success_init, _ = _execute_git_command(['init'], cwd=repo_path, task_name=task_name)
            if not success_init:
                return False
            if origin_url:
                log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
                _, success_add_remote, _ = _execute_git_command(['remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name)
                if not success_add_remote:
                    return False
            log(MESSAGES["git_repo_initialized"], level='success', task_name=task_name)
        else:
            log(MESSAGES["git_not_repo_and_not_init"].format(repo_path), level='error', task_name=task_name)
            return False
    elif origin_url:
        # Check if origin already exists and has the correct URL
        stdout_remotes, success_remotes, _ = _execute_git_command(['remote', '-v'], cwd=repo_path, task_name=task_name, log_level='debug')
        if not success_remotes: # Failed to list remotes
            return False
        
        origin_exists = False
        for line in stdout_remotes.splitlines():
            if line.startswith('origin') and origin_url in line:
                origin_exists = True
                break
        
        if not origin_exists:
            log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
            _, success_add_remote, _ = _execute_git_command(['remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name)
            if not success_add_remote:
                return False

    # Checkout or switch to the specified branch
    log(MESSAGES["git_checking_out_branch"].format(branch), level='step', task_name=task_name)
    
    # --- UPDATED LOGIC FOR LOCAL BRANCH EXISTENCE CHECK ---
    # Use 'git rev-parse --verify' to reliably check if a local branch exists
    _, local_branch_exists, _ = _execute_git_command(['rev-parse', '--verify', branch], cwd=repo_path, task_name=task_name, log_level='debug')

    if local_branch_exists:
        log(MESSAGES["git_branch_found_local"].format(branch), level='info', task_name=task_name)
        _, checkout_success, _ = _execute_git_command(['checkout', branch], cwd=repo_path, task_name=task_name)
        if not checkout_success:
            log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
            return False
    else:
        log(MESSAGES["git_branch_not_found_local"].format(branch), level='info', task_name=task_name)
        # Try checking out a remote tracking branch if it exists remotely
        stdout_remote_branches, success_remote_branches, _ = _execute_git_command(['ls-remote', '--heads', 'origin', branch], cwd=repo_path, task_name=task_name, log_level='debug')
        
        remote_branch_exists = success_remote_branches and f'refs/heads/{branch}' in stdout_remote_branches

        if remote_branch_exists:
            log(MESSAGES["git_branch_found_remote"].format(branch, 'origin'), level='info', task_name=task_name)
            _, checkout_track_success, _ = _execute_git_command(['checkout', '--track', f'origin/{branch}'], cwd=repo_path, task_name=task_name)
            if not checkout_track_success:
                log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
                return False
        else: # If not found locally or remotely, create new branch
            log(MESSAGES["git_branch_not_found_local_or_remote"].format(branch), level='info', task_name=task_name)
            _, create_branch_success, _ = _execute_git_command(['checkout', '-b', branch], cwd=repo_path, task_name=task_name)
            if not create_branch_success:
                log(MESSAGES["git_branch_creation_failed"].format(branch), level='error', task_name=task_name)
                return False
            # Push new branch to set upstream
            if origin_url:
                log(MESSAGES["git_pushing_new_branch"].format(branch, 'origin', branch), level='normal', task_name=task_name)
                _, push_new_branch_success, _ = _execute_git_command(['push', '-u', 'origin', branch], cwd=repo_path, task_name=task_name)
                if not push_new_branch_success:
                    log(MESSAGES["git_push_new_branch_failed_warning"].format(branch, 'origin', branch), level='warning', task_name=task_name)
                    # Don't return False, as local branch is created
    # --- END UPDATED LOGIC ---
        
    log(MESSAGES["git_on_branch"].format(branch), level='success', task_name=task_name)

    # Flag to track if the repo is clean after pull (and potential stash pop)
    repo_clean_after_pull = False 

    # Pull latest changes if configured
    if task.pull_before_command:
        log(MESSAGES["git_pulling_latest"], level='step', task_name=task_name)
        
        has_local_changes_before_pull, check_error = _check_for_changes(repo_path, task_name)
        if check_error: return False
        
        stashed = False
        if has_local_changes_before_pull:
            log(MESSAGES["workflow_local_changes_found_stashing"], level='info', task_name=task_name)
            if not _stash_local_changes(repo_path, task_name): return False
            stashed = True
        else:
            log(MESSAGES["workflow_no_local_changes_to_stash"], level='info', task_name=task_name)

        _, pull_success, _ = _execute_git_command(['pull', 'origin', branch], cwd=repo_path, task_name=task_name)
        if not pull_success:
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
        
        # --- NEW: Check for changes AFTER pull and pop ---
        has_changes_after_pull, check_error_after_pull = _check_for_changes(repo_path, task_name)
        if check_error_after_pull: return False # Error checking changes after pull
        
        if not has_changes_after_pull:
            repo_clean_after_pull = True
            log(MESSAGES["git_repo_already_up_to_date_skip_actions"], level='info', task_name=task_name)
        # --- END NEW ---
    else:
        log(MESSAGES["workflow_pull_before_command_skipped"], level='info', task_name=task_name)

    # --- NEW: Conditional execution of pre_command, add, commit, push, post_command ---
    if not repo_clean_after_pull:
        # Execute pre-command
        if task.pre_command:
            log(MESSAGES["workflow_executing_pre_command"], level='step', task_name=task_name)
            if not _execute_command(task.pre_command, cwd=repo_path, task_name=task_name):
                log(MESSAGES["workflow_pre_command_failed"], level='error', task_name=task_name)
                return False
            log(MESSAGES["workflow_pre_command_successful"], level='success', task_name=task_name)

        # Add all changes and commit
        log(MESSAGES["git_adding_changes"], level='step', task_name=task_name)
        _, add_success, _ = _execute_git_command(['add', '.'], cwd=repo_path, task_name=task_name)
        if not add_success:
            return False
        log(MESSAGES["git_changes_added"], level='success', task_name=task_name)

        log(MESSAGES["git_committing_changes"], level='step', task_name=task_name)
        
        # --- CONSTRUCT COMMIT MESSAGE WITH TIMESTAMP ---
        final_commit_message = task.commit_message
        if task.timestamp_format:
            timestamp_str = datetime.now().strftime(task.timestamp_format)
            final_commit_message = f"{task.commit_message} [{timestamp_str}]"
        # --- END CONSTRUCT COMMIT MESSAGE ---

        # --- Capture the commit_made flag ---
        _, commit_success, commit_made = _execute_git_command(['commit', '-m', final_commit_message], cwd=repo_path, task_name=task_name)
        log(f"DEBUG: commit_made value: {repr(commit_made)} (type: {type(commit_made)})", level='debug', task_name=task_name)
        if not commit_success:
            return False # Genuine commit error
        # --- End capture ---
            
        # Push changes if configured
        if task.push_after_command:
            # --- NEW: Only push if a commit was actually made ---
            if commit_made:
                log(MESSAGES["git_pushing_changes"].format(branch), level='step', task_name=task_name)
                _, push_success, _ = _execute_git_command(['push', 'origin', branch], cwd=repo_path, task_name=task_name)
                if not push_success:
                    return False
                log(MESSAGES["git_push_successful"], level='success', task_name=task_name)
            else:
                log(MESSAGES["git_push_skipped_no_new_commit"], level='info', task_name=task_name)
            # --- END NEW ---

        # Execute post-command
        if task.post_command:
            log(MESSAGES["workflow_executing_post_command"], level='step', task_name=task_name)
            if not _execute_command(task.post_command, cwd=repo_path, task_name=task_name):
                log(MESSAGES["workflow_post_command_failed"], level='error', task_name=task_name)
                return False
            log(MESSAGES["workflow_post_command_successful"], level='success', task_name=task_name)
    else:
        # If repo is clean after pull, but pre_command or post_command are defined,
        # we should log that they are skipped, rather than executing them.
        # This aligns with the intention of skipping further actions if the repo is already up-to-date.
        if task.pre_command or task.post_command:
             log(MESSAGES["update_skipping_pre_post_commands"], level='info', task_name=task_name)


    # --- END NEW CONDITIONAL EXECUTION ---

    log(MESSAGES["workflow_completed"].format(task_name), level='success', task_name=task_name)
    return True


def run_update_task_workflow(args: SimpleNamespace, task: SimpleNamespace, config_file_path: str):
    """
    Executes a simplified update workflow focused on pull/commit/push.
    This version implicitly skips pre_command and post_command (now explicitly handled
    by the `repo_clean_after_pull` check and the message below).
    """
    task_name = task.name

    log(MESSAGES["update_workflow_start"].format(task_name), level='info', task_name=task_name)

    # --- FIX: Prioritize command-line overrides ---
    repo_path = args.folder if args.folder else task.folder
    branch = args.branch if args.branch else task.branch
    origin_url = args.origin if args.origin else task.origin
    # --- END FIX ---

    # Ensure repository directory exists and is a Git repo
    if not os.path.exists(repo_path):
        log(MESSAGES["update_error_folder_not_found"].format(repo_path), level='error', task_name=task_name)
        return False
    if not _is_git_repo(repo_path):
        log(MESSAGES["update_error_not_git_repo"].format(repo_path), level='error', task_name=task_name)
        return False
    
    # Ensure origin is set if it was defined in config
    if origin_url: # Use origin_url from combined args/task
        log(MESSAGES["git_checking_remote"].format(origin_url), level='debug', task_name=task_name)
        # Check if origin is already set or add it
        stdout_remotes, success_remotes, _ = _execute_git_command(['remote', '-v'], cwd=repo_path, task_name=task_name, log_level='debug')
        if not success_remotes: # Failed to list remotes
            return False
        
        origin_exists = False
        for line in stdout_remotes.splitlines():
            if line.startswith('origin') and origin_url in line:
                origin_exists = True
                break
        
        if not origin_exists:
            log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
            _, success_add_remote, _ = _execute_git_command(['remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name)
            if not success_add_remote:
                return False

    # Checkout or switch to the specified branch
    log(MESSAGES["git_checking_out_branch"].format(branch), level='step', task_name=task_name)
    
    # --- UPDATED LOGIC FOR LOCAL BRANCH EXISTENCE CHECK (again for update workflow) ---
    # Use 'git rev-parse --verify' to reliably check if a local branch exists
    _, local_branch_exists, _ = _execute_git_command(['rev-parse', '--verify', branch], cwd=repo_path, task_name=task_name, log_level='debug')

    if local_branch_exists:
        log(MESSAGES["git_branch_found_local"].format(branch), level='info', task_name=task_name)
        _, checkout_success, _ = _execute_git_command(['checkout', branch], cwd=repo_path, task_name=task_name)
        if not checkout_success:
            log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
            return False
    else:
        log(MESSAGES["git_branch_not_found_local"].format(branch), level='info', task_name=task_name)
        # Try checking out a remote tracking branch if it exists remotely
        stdout_remote_branches, success_remote_branches, _ = _execute_git_command(['ls-remote', '--heads', 'origin', branch], cwd=repo_path, task_name=task_name, log_level='debug')
        
        remote_branch_exists = success_remote_branches and f'refs/heads/{branch}' in stdout_remote_branches

        if remote_branch_exists:
            log(MESSAGES["git_branch_found_remote"].format(branch, 'origin'), level='info', task_name=task_name)
            _, checkout_track_success, _ = _execute_git_command(['checkout', '--track', f'origin/{branch}'], cwd=repo_path, task_name=task_name)
            if not checkout_track_success:
                log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
                return False
        else: # If not found locally or remotely, create new branch
            log(MESSAGES["git_branch_not_found_local_or_remote"].format(branch), level='info', task_name=task_name)
            _, create_branch_success, _ = _execute_git_command(['checkout', '-b', branch], cwd=repo_path, task_name=task_name)
            if not create_branch_success:
                log(MESSAGES["git_branch_creation_failed"].format(branch), level='error', task_name=task_name)
                return False
            # Push new branch to set upstream
            if origin_url:
                log(MESSAGES["git_pushing_new_branch"].format(branch, 'origin', branch), level='normal', task_name=task_name)
                _, push_new_branch_success, _ = _execute_git_command(['push', '-u', 'origin', branch], cwd=repo_path, task_name=task_name)
                if not push_new_branch_success:
                    log(MESSAGES["git_push_new_branch_failed_warning"].format(branch, 'origin', branch), level='warning', task_name=task_name)
                    # Don't return False, as local branch is created
    # --- END UPDATED LOGIC (for update workflow) ---
        
    log(MESSAGES["git_on_branch"].format(branch), level='success', task_name=task_name)

    # Flag to track if the repo is clean after pull (and potential stash pop)
    repo_clean_after_pull = False

    # --- START STASH/PULL/POP LOGIC FOR UPDATE WORKFLOW ---
    log(MESSAGES["git_pulling_latest"], level='step', task_name=task_name)
    
    has_local_changes_before_pull, check_error = _check_for_changes(repo_path, task_name)
    if check_error: return False
    
    stashed = False
    if has_local_changes_before_pull:
        log(MESSAGES["workflow_local_changes_found_stashing"], level='info', task_name=task_name)
        if not _stash_local_changes(repo_path, task_name): return False
        stashed = True
    else:
        log(MESSAGES["workflow_no_local_changes_to_stash"], level='info', task_name=task_name)

    _, pull_success, _ = _execute_git_command(['pull', 'origin', branch], cwd=repo_path, task_name=task_name)
    if not pull_success:
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
    
    # --- NEW: Check for changes AFTER pull and pop ---
    has_changes_after_pull, check_error_after_pull = _check_for_changes(repo_path, task_name)
    if check_error_after_pull: return False # Error checking changes after pull
    
    if not has_changes_after_pull:
        repo_clean_after_pull = True
        log(MESSAGES["git_repo_already_up_to_date_skip_actions"], level='info', task_name=task_name)
    # --- END NEW ---

    # Pre-command and post-command are explicitly skipped in update workflow
    # This message is now slightly redundant due to the new logic but kept for clarity if `repo_clean_after_pull` is false
    log(MESSAGES["update_skipping_pre_post_commands"], level='info', task_name=task_name)

    # --- NEW: Conditional execution of add, commit, push ---
    if not repo_clean_after_pull:
        # Add all changes and commit
        log(MESSAGES["git_adding_changes"], level='step', task_name=task_name)
        _, add_success, _ = _execute_git_command(['add', '.'], cwd=repo_path, task_name=task_name)
        if not add_success:
            return False
        log(MESSAGES["git_changes_added"], level='success', task_name=task_name)

        log(MESSAGES["git_committing_changes"], level='step', task_name=task_name)
        
        # --- CONSTRUCT COMMIT MESSAGE WITH TIMESTAMP ---
        final_commit_message = task.commit_message
        if task.timestamp_format:
            timestamp_str = datetime.now().strftime(task.timestamp_format)
            final_commit_message = f"{task.commit_message} [{timestamp_str}]"
        # --- END CONSTRUCT COMMIT MESSAGE ---

        # --- Capture the commit_made flag ---
        _, commit_success, commit_made = _execute_git_command(['commit', '-m', final_commit_message], cwd=repo_path, task_name=task_name)
        log(f"DEBUG: commit_made value: {repr(commit_made)} (type: {type(commit_made)})", level='debug', task_name=task_name)
        if not commit_success:
            return False # Genuine commit error
        # --- End capture ---
        
        # Push changes if configured
        if task.push_after_command:
            # --- NEW: Only push if a commit was actually made ---
            if commit_made:
                log(MESSAGES["git_pushing_changes"].format(branch), level='step', task_name=task_name)
                _, push_success, _ = _execute_git_command(['push', 'origin', branch], cwd=repo_path, task_name=task_name)
                if not push_success:
                    return False
                log(MESSAGES["git_push_successful"], level='success', task_name=task_name)
            else:
                log(MESSAGES["git_push_skipped_no_new_commit"], level='info', task_name=task_name)
            # --- END NEW ---
    # --- END NEW CONDITIONAL EXECUTION ---

    log(MESSAGES["update_workflow_completed"].format(task_name), level='success', task_name=task_name)
    return True

# --- NEW: run_pull_workflow ---
def run_pull_workflow(args: SimpleNamespace, task: SimpleNamespace):
    """
    Executes a pull-only workflow with automatic stash/pop.
    Skips pre/post commands, add, commit, and push.
    """
    task_name = task.name

    log(MESSAGES["pull_workflow_start"].format(task_name), level='info', task_name=task_name)

    # Prioritize command-line overrides for folder, branch, origin
    repo_path = args.folder if args.folder else task.folder
    branch = args.branch if args.branch else task.branch
    origin_url = args.origin if args.origin else task.origin

    # Ensure repository directory exists and is a Git repo
    if not os.path.exists(repo_path):
        log(MESSAGES["update_error_folder_not_found"].format(repo_path), level='error', task_name=task_name)
        return False
    if not _is_git_repo(repo_path):
        log(MESSAGES["update_error_not_git_repo"].format(repo_path), level='error', task_name=task_name)
        return False
    
    # Ensure origin is set if it was defined in config (or overridden)
    if origin_url:
        log(MESSAGES["git_checking_remote"].format(origin_url), level='debug', task_name=task_name)
        stdout_remotes, success_remotes, _ = _execute_git_command(['remote', '-v'], cwd=repo_path, task_name=task_name, log_level='debug')
        if not success_remotes or origin_url not in stdout_remotes:
            log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
            _, success_add_remote, _ = _execute_git_command(['remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name)
            if not success_add_remote:
                return False

    # Checkout or switch to the specified branch
    log(MESSAGES["git_checking_out_branch"].format(branch), level='step', task_name=task_name)
    
    _, local_branch_exists, _ = _execute_git_command(['rev-parse', '--verify', branch], cwd=repo_path, task_name=task_name, log_level='debug')

    if local_branch_exists:
        log(MESSAGES["git_branch_found_local"].format(branch), level='info', task_name=task_name)
        _, checkout_success, _ = _execute_git_command(['checkout', branch], cwd=repo_path, task_name=task_name)
        if not checkout_success:
            log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
            return False
    else:
        log(MESSAGES["git_branch_not_found_local"].format(branch), level='info', task_name=task_name)
        stdout_remote_branches, success_remote_branches, _ = _execute_git_command(['ls-remote', '--heads', 'origin', branch], cwd=repo_path, task_name=task_name, log_level='debug')
        
        remote_branch_exists = success_remote_branches and f'refs/heads/{branch}' in stdout_remote_branches

        if remote_branch_exists:
            log(MESSAGES["git_branch_found_remote"].format(branch, 'origin'), level='info', task_name=task_name)
            _, checkout_track_success, _ = _execute_git_command(['checkout', '--track', f'origin/{branch}'], cwd=repo_path, task_name=task_name)
            if not checkout_track_success:
                log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
                return False
        else:
            log(MESSAGES["git_branch_not_found_local_or_remote"].format(branch), level='info', task_name=task_name)
            _, create_branch_success, _ = _execute_git_command(['checkout', '-b', branch], cwd=repo_path, task_name=task_name)
            if not create_branch_success:
                log(MESSAGES["git_branch_creation_failed"].format(branch), level='error', task_name=task_name)
                return False
            if origin_url:
                log(MESSAGES["git_pushing_new_branch"].format(branch, 'origin', branch), level='normal', task_name=task_name)
                _, push_new_branch_success, _ = _execute_git_command(['push', '-u', 'origin', branch], cwd=repo_path, task_name=task_name)
                if not push_new_branch_success:
                    log(MESSAGES["git_push_new_branch_failed_warning"].format(branch, 'origin', branch), level='warning', task_name=task_name)
        
    log(MESSAGES["git_on_branch"].format(branch), level='success', task_name=task_name)

    # Perform pull with stash/pop
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

    _, pull_success, _ = _execute_git_command(['pull', 'origin', branch], cwd=repo_path, task_name=task_name)
    if not pull_success:
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
    
    log(MESSAGES["pull_workflow_completed"].format(task_name), level='success', task_name=task_name)
    return True  