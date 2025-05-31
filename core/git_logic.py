import subprocess
import os
from datetime import datetime
from core.logger import log
from core.messages import MESSAGES

def run_git_command(repo_path, command_args, task_name, capture_output=False):
    """
    Helper function to run a git command.
    Logs command execution and output at 'normal' level, errors at 'error' level.
    """
    log(MESSAGES["git_executing_command"].format(' '.join(command_args), repo_path), level='normal', task_name=task_name)
    try:
        process = subprocess.run(
            ["git"] + command_args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False
        )

        if process.stdout:
            log(MESSAGES["git_stdout"].format(process.stdout.strip()), level='normal', task_name=task_name)
        if process.stderr:
            log(MESSAGES["git_stderr"].format(process.stderr.strip()), level='normal', task_name=task_name)

        if process.returncode != 0:
            log(MESSAGES["git_command_failed"].format(process.returncode), level='error', task_name=task_name)
            return None # Indicate failure
        return process.stdout.strip() if capture_output else True
    except FileNotFoundError:
        log(MESSAGES["git_error_not_found"], level='error', task_name=task_name)
        return None
    except Exception as e:
        log(MESSAGES["git_error_unexpected"].format(e), level='error', task_name=task_name)
        return None

def pull_updates(repo_path, branch, task_name):
    """
    Performs a git pull on the specified branch and origin.
    Logs at 'normal' level for non-critical information.
    """
    log(MESSAGES["git_pulling_updates"].format(branch), level='normal', task_name=task_name)
    result = run_git_command(repo_path, ["pull", "origin", branch], task_name)
    if result is None:
        log(MESSAGES["git_pull_failed"].format(branch), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_pull_successful"], level='normal', task_name=task_name)
    return True

def diff_changes(repo_path, task_name):
    """
    Checks for any changes (modified, untracked, deleted, etc.) in the Git repository.
    Logs at 'normal' level for non-critical information.
    """
    log(MESSAGES["git_checking_status"], level='normal', task_name=task_name)
    output = run_git_command(repo_path, ["status", "--porcelain"], task_name, capture_output=True)

    if output is None:
        log(MESSAGES["git_error_status_check"], level='error', task_name=task_name)
        return None
    elif output:
        log(MESSAGES["git_changes_detected"], level='normal', task_name=task_name)
        return True
    else:
        log(MESSAGES["git_no_changes_detected"], level='normal', task_name=task_name)
        return False

def add_commit_changes(repo_path, commit_message, files_to_add, task_name):
    """
    Stages specified files and commits them to the repository.
    Appends a timestamp to the commit message.
    Logs at 'normal' level for non-critical information.
    """
    timestamp = datetime.now().strftime("%m%d%H%M%S") # MMDDHHMMSS
    final_commit_message = f"{commit_message} [{timestamp}]"

    log(MESSAGES["git_staging_changes"].format(files_to_add), level='normal', task_name=task_name)
    add_result = run_git_command(repo_path, ["add", files_to_add], task_name)
    if add_result is None:
        log(MESSAGES["git_add_failed"], level='error', task_name=task_name)
        return False

    log(MESSAGES["git_committing_changes"].format(final_commit_message), level='normal', task_name=task_name)
    commit_result = run_git_command(repo_path, ["commit", "-m", final_commit_message], task_name)
    if commit_result is None:
        log(MESSAGES["git_commit_failed"], level='error', task_name=task_name)
        return False

    log(MESSAGES["git_add_commit_successful"], level='normal', task_name=task_name)
    return True

def push_updates(repo_path, branch, origin, task_name):
    """
    Pushes committed changes to the specified remote origin and branch.
    Logs at 'normal' level for non-critical information.
    """
    log(MESSAGES["git_pushing_changes"].format(origin, branch), level='normal', task_name=task_name)
    push_result = run_git_command(repo_path, ["push", origin, branch], task_name)
    if push_result is None:
        log(MESSAGES["git_push_failed"].format(origin, branch), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_push_successful"], level='normal', task_name=task_name)
    return True

def initialize_repo(repo_path, origin_url=None, task_name=None):
    """
    Initializes a Git repository in the given path.
    If origin_url is provided, it also adds the remote origin.
    """
    git_dir = os.path.join(repo_path, '.git')
    if os.path.exists(git_dir):
        log(MESSAGES["git_repo_already_exists"].format(repo_path), level='normal', task_name=task_name)
        return True

    log(MESSAGES["git_initializing_repo"].format(repo_path), level='step', task_name=task_name)
    if not os.path.exists(repo_path):
        try:
            os.makedirs(repo_path, exist_ok=True)
            log(MESSAGES["git_created_dir_for_repo"].format(repo_path), level='normal', task_name=task_name)
        except Exception as e:
            log(MESSAGES["git_error_creating_dir"].format(repo_path, e), level='error', task_name=task_name)
            return False

    init_result = run_git_command(repo_path, ["init"], task_name)
    if init_result is None:
        log(MESSAGES["git_init_failed"].format(repo_path), level='error', task_name=task_name)
        return False
    log(MESSAGES["git_init_successful"].format(repo_path), level='normal', task_name=task_name)

    if origin_url:
        log(MESSAGES["git_adding_remote_origin"].format(origin_url), level='normal', task_name=task_name)
        add_remote_result = run_git_command(repo_path, ["remote", "add", "origin", origin_url], task_name)
        if add_remote_result is None:
            log(MESSAGES["git_add_remote_failed"].format(origin_url), level='error', task_name=task_name)
            return False
        log(MESSAGES["git_add_remote_successful"].format(origin_url), level='normal', task_name=task_name)
    
    return True

def checkout_or_create_branch(repo_path, branch_name, origin_name, task_name):
    """
    Checks if a branch exists on the remote, checks it out if it does,
    otherwise creates it locally.
    """
    log(MESSAGES["git_checkout_or_create_branch_step"].format(branch_name), level='step', task_name=task_name)

    log(MESSAGES["git_fetching_remote"].format(origin_name), level='normal', task_name=task_name)
    fetch_result = run_git_command(repo_path, ["fetch", origin_name], task_name)
    if fetch_result is None:
        log(MESSAGES["git_fetch_failed_warning"].format(origin_name), level='warning', task_name=task_name)
    
    remote_branch_check = run_git_command(repo_path, ["ls-remote", "--heads", origin_name, branch_name], task_name, capture_output=True)
    
    branch_exists_remotely = False
    if remote_branch_check is not None and remote_branch_check.strip():
        branch_exists_remotely = True
        log(MESSAGES["git_branch_found_remote"].format(branch_name, origin_name), level='normal', task_name=task_name)
    else:
        log(MESSAGES["git_branch_not_found_remote"].format(branch_name, origin_name), level='normal', task_name=task_name)

    local_branch_check = run_git_command(repo_path, ["branch", "--list", branch_name], task_name, capture_output=True)
    branch_exists_locally = False
    if local_branch_check is not None and local_branch_check.strip():
        branch_exists_locally = True
        log(MESSAGES["git_branch_found_local"].format(branch_name), level='normal', task_name=task_name)
    else:
        log(MESSAGES["git_branch_not_found_local"].format(branch_name), level='normal', task_name=task_name)

    if branch_exists_remotely or branch_exists_locally:
        log(MESSAGES["git_attempting_checkout_existing"].format(branch_name), level='normal', task_name=task_name)
        checkout_result = run_git_command(repo_path, ["checkout", branch_name], task_name)
        if checkout_result is None:
            log(MESSAGES["git_checkout_failed"].format(branch_name), level='error', task_name=task_name)
            return False
        log(MESSAGES["git_checkout_successful"].format(branch_name), level='normal', task_name=task_name)
        
        if branch_exists_remotely and not run_git_command(repo_path, ["branch", "--set-upstream-to", f"{origin_name}/{branch_name}", branch_name], task_name):
             log(MESSAGES["git_warning_set_upstream_failed"].format(branch_name, origin_name, branch_name), level='warning', task_name=task_name)

    else:
        log(MESSAGES["git_creating_new_branch"].format(branch_name), level='normal', task_name=task_name)
        create_result = run_git_command(repo_path, ["checkout", "-b", branch_name], task_name)
        if create_result is None:
            log(MESSAGES["git_create_branch_failed"].format(branch_name), level='error', task_name=task_name)
            return False
        log(MESSAGES["git_create_checkout_successful"].format(branch_name), level='normal', task_name=task_name)

        if origin_name:
            log(MESSAGES["git_pushing_new_branch"].format(branch_name, origin_name), level='normal', task_name=task_name)
            push_new_branch_result = run_git_command(repo_path, ["push", "-u", origin_name, branch_name], task_name)
            if push_new_branch_result is None:
                log(MESSAGES["git_push_new_branch_failed_warning"].format(branch_name, origin_name), level='warning', task_name=task_name)

    log(MESSAGES["git_branch_op_completed"].format(branch_name), level='success', task_name=task_name)
    return True