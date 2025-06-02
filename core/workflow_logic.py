import subprocess
import os
import shutil
from types import SimpleNamespace

from core.logger import log
from core.messages import MESSAGES

def _is_git_repo(folder_path):
    """Checks if the given folder is a Git repository."""
    return os.path.isdir(os.path.join(folder_path, '.git'))

def _execute_git_command(command_parts, cwd, task_name, log_level='info'):
    """Executes a Git command and logs its output."""
    cmd_str = " ".join(command_parts)
    log(MESSAGES["git_executing_command"].format(cmd_str), level='debug', task_name=task_name)
    try:
        result = subprocess.run(
            command_parts,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                log(f"  OUT: {line}", level='debug', task_name=task_name)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                log(f"  ERR: {line}", level='debug', task_name=task_name) # Git stderr often contains info
        return True
    except subprocess.CalledProcessError as e:
        # --- START CHANGES HERE ---
        # Check if the error is due to "nothing to commit" for a git commit command
        if command_parts[0] == 'git' and command_parts[1] == 'commit':
            # Check for Portuguese and English "nothing to commit" messages
            # Git sends this message to stdout even on error exit code 1
            output_combined = (e.stdout or "") + (e.stderr or "")
            if "nada a memorizar, árvore-trabalho limpa" in output_combined or \
               "nothing to commit, working tree clean" in output_combined or \
               "no changes added to commit" in output_combined: # Another common message
                log(MESSAGES["git_no_changes_to_commit"], level='info', task_name=task_name)
                # Still log the output as debug for full context in the log file
                if e.stdout:
                    for line in e.stdout.strip().splitlines():
                        log(f"  OUT: {line}", level='debug', task_name=task_name)
                if e.stderr:
                    for line in e.stderr.strip().splitlines():
                        log(f"  ERR: {line}", level='debug', task_name=task_name)
                return True # Treat "no changes" as a successful, albeit non-op, commit
        
        # If it's not a "nothing to commit" error, or not a commit command, log as actual error
        log(MESSAGES["git_command_failed"].format(cmd_str, e.returncode), level='error', task_name=task_name)
        if e.stdout:
            for line in e.stdout.strip().splitlines():
                log(f"  OUT: {line}", level='error', task_name=task_name)
        if e.stderr:
            for line in e.stderr.strip().splitlines():
                log(f"  ERR: {line}", level='error', task_name=task_name)
        return False
        # --- END CHANGES HERE ---
    except FileNotFoundError:
        log(MESSAGES["git_not_found"], level='error', task_name=task_name)
        return False
    except Exception as e:
        log(MESSAGES["git_command_exception"].format(cmd_str, e), level='error', task_name=task_name)
        return False

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
            return

    # Check if it's a Git repository and initialize if needed
    if not _is_git_repo(repo_path):
        if args.initialize:
            log(MESSAGES["git_initializing_repo"].format(repo_path), level='step', task_name=task_name)
            if not _execute_git_command(['git', 'init'], cwd=repo_path, task_name=task_name):
                return
            if origin_url:
                log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
                if not _execute_git_command(['git', 'remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name):
                    return
            log(MESSAGES["git_repo_initialized"], level='success', task_name=task_name)
        else:
            log(MESSAGES["git_not_repo_and_not_init"].format(repo_path), level='error', task_name=task_name)
            return
    elif origin_url and not _execute_git_command(['git', 'remote', 'get-url', 'origin'], cwd=repo_path, task_name=task_name):
        # If it is a git repo but no origin set, add it
        log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
        if not _execute_git_command(['git', 'remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name):
            return

    # Checkout or switch to the specified branch
    log(MESSAGES["git_checking_out_branch"].format(branch), level='step', task_name=task_name)
    if not _execute_git_command(['git', 'checkout', branch], cwd=repo_path, task_name=task_name):
        # If checkout fails, try to create and checkout the branch
        log(MESSAGES["git_branch_checkout_failed_try_create"].format(branch), level='warning', task_name=task_name)
        if not _execute_git_command(['git', 'checkout', '-b', branch], cwd=repo_path, task_name=task_name):
            log(MESSAGES["git_branch_creation_failed"].format(branch), level='error', task_name=task_name)
            return
    log(MESSAGES["git_on_branch"].format(branch), level='success', task_name=task_name)

    # Pull latest changes if configured
    if task.pull_before_command:
        log(MESSAGES["git_pulling_latest"], level='step', task_name=task_name)
        if not _execute_git_command(['git', 'pull', 'origin', branch], cwd=repo_path, task_name=task_name):
            return
        log(MESSAGES["git_pull_successful"], level='success', task_name=task_name)

    # Execute pre-command
    if task.pre_command:
        log(MESSAGES["workflow_executing_pre_command"], level='step', task_name=task_name)
        if not _execute_command(task.pre_command, cwd=repo_path, task_name=task_name):
            log(MESSAGES["workflow_pre_command_failed"], level='error', task_name=task_name)
            return
        log(MESSAGES["workflow_pre_command_successful"], level='success', task_name=task_name)

    # Add all changes and commit
    log(MESSAGES["git_adding_changes"], level='step', task_name=task_name)
    if not _execute_git_command(['git', 'add', '.'], cwd=repo_path, task_name=task_name):
        return
    log(MESSAGES["git_changes_added"], level='success', task_name=task_name)

    log(MESSAGES["git_committing_changes"], level='step', task_name=task_name)
    # The _execute_git_command function now handles the "no changes to commit" gracefully
    if not _execute_git_command(['git', 'commit', '-m', task.commit_message], cwd=repo_path, task_name=task_name):
        # If it returns False here, it means it was a genuine commit error, not just "no changes"
        return
    else:
        # If it returned True, either a commit was made, or there were no changes (which is handled gracefully)
        # We don't need to specifically log 'changes committed' here as _execute_git_command handles "no changes"
        pass


    # Push changes if configured
    if task.push_after_command:
        log(MESSAGES["git_pushing_changes"].format(branch), level='step', task_name=task_name)
        if not _execute_git_command(['git', 'push', 'origin', branch], cwd=repo_path, task_name=task_name):
            return
        log(MESSAGES["git_push_successful"], level='success', task_name=task_name)

    # Execute post-command
    if task.post_command:
        log(MESSAGES["workflow_executing_post_command"], level='step', task_name=task_name)
        if not _execute_command(task.post_command, cwd=repo_path, task_name=task_name):
            log(MESSAGES["workflow_post_command_failed"], level='error', task_name=task_name)
            return
        log(MESSAGES["workflow_post_command_successful"], level='success', task_name=task_name)

    log(MESSAGES["workflow_completed"].format(task_name), level='success', task_name=task_name)


def run_update_task_workflow(args: SimpleNamespace, task: SimpleNamespace, config_file_path: str):
    """
    Executes a simplified update workflow focused on pull/commit/push.
    This version skips pre_command and post_command.
    """
    task_name = task.name

    log(MESSAGES["update_workflow_start"].format(task_name), level='info', task_name=task_name)

    repo_path = task.folder
    branch = task.branch
    origin_url = task.origin

    # Ensure repository directory exists and is a Git repo
    if not os.path.exists(repo_path):
        log(MESSAGES["update_error_folder_not_found"].format(repo_path), level='error', task_name=task_name)
        return
    if not _is_git_repo(repo_path):
        log(MESSAGES["update_error_not_git_repo"].format(repo_path), level='error', task_name=task_name)
        return
    
    # Ensure origin is set if it was defined in config
    if origin_url:
        log(MESSAGES["git_checking_remote"].format(origin_url), level='debug', task_name=task_name)
        # Check if origin is already set or add it
        result = subprocess.run(['git', 'remote', '-v'], cwd=repo_path, capture_output=True, text=True)
        if origin_url not in result.stdout:
            log(MESSAGES["git_adding_remote"].format(origin_url), level='step', task_name=task_name)
            if not _execute_git_command(['git', 'remote', 'add', 'origin', origin_url], cwd=repo_path, task_name=task_name):
                return

    # Checkout or switch to the specified branch
    log(MESSAGES["git_checking_out_branch"].format(branch), level='step', task_name=task_name)
    if not _execute_git_command(['git', 'checkout', branch], cwd=repo_path, task_name=task_name):
        log(MESSAGES["git_branch_checkout_failed"].format(branch), level='error', task_name=task_name)
        return
    log(MESSAGES["git_on_branch"].format(branch), level='success', task_name=task_name)

    # Pull latest changes (always perform pull in update mode)
    log(MESSAGES["git_pulling_latest"], level='step', task_name=task_name)
    if not _execute_git_command(['git', 'pull', 'origin', branch], cwd=repo_path, task_name=task_name):
        return
    log(MESSAGES["git_pull_successful"], level='success', task_name=task_name)

    # Add all changes and commit
    log(MESSAGES["git_adding_changes"], level='step', task_name=task_name)
    if not _execute_git_command(['git', 'add', '.'], cwd=repo_path, task_name=task_name):
        return
    log(MESSAGES["git_changes_added"], level='success', task_name=task_name)

    log(MESSAGES["git_committing_changes"], level='step', task_name=task_name)
    # The _execute_git_command function now handles the "no changes to commit" gracefully
    if not _execute_git_command(['git', 'commit', '-m', task.commit_message], cwd=repo_path, task_name=task_name):
        # If it returns False here, it means it was a genuine commit error, not just "no changes"
        return
    else:
        # If it returned True, either a commit was made, or there were no changes (which is handled gracefully)
        # We don't need to specifically log 'changes committed' here as _execute_git_command handles "no changes"
        pass

    # Push changes (always perform push in update mode)
    if task.push_after_command:
        log(MESSAGES["git_pushing_changes"].format(branch), level='step', task_name=task_name)
        if not _execute_git_command(['git', 'push', 'origin', branch], cwd=repo_path, task_name=task_name):
            return
        log(MESSAGES["git_push_successful"], level='success', task_name=task_name)

    log(MESSAGES["update_workflow_completed"].format(task_name), level='success', task_name=task_name)