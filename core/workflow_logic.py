# core/workflow_logic.py

import os
from core.logger import log
from core.messages import MESSAGES
from core.git_logic import (
    is_git_repo, init_repo, add_remote, checkout_or_create_branch,
    pull_updates, check_for_changes, git_add_commit, git_push,
    stash_local_changes, pop_stashed_changes
)
from core.command_logic import execute_command

def run_task_workflow(args, task, config_file_path):
    """
    Runs the standard Git automation task workflow.
    
    Args:
        args (argparse.Namespace): The parsed command-line arguments.
        task (dict): The task configuration loaded from the JSON file.
        config_file_path (str): The path to the task's configuration file.
    """
    task_name = task.get("name", "Unnamed Task")
    log_prefix = f"[{task_name}]"

    log(MESSAGES["workflow_start_task"].format(config_file_path), level='step', task_name=task_name)

    # --- 1. Get and confirm configuration values ---
    git_repo_path = args.folder if args.folder is not None else task.get("git_repo_path")
    branch = args.branch if args.branch is not None else task.get("branch", "main")
    origin = args.origin if args.origin is not None else task.get("origin")
    command_line = task.get("command_line", "")
    git_commit_message = task.get("git_commit_message", f"Automated update for {task_name}")

    if not git_repo_path:
        log(MESSAGES["workflow_error_missing_repo_path"].format(task_name), level='error', task_name=task_name)
        log(MESSAGES["workflow_task_aborted_missing_info"].format(task_name), level='error', task_name=task_name)
        return False

    log(MESSAGES["workflow_task_details"].format(task_name), level='normal')
    log(MESSAGES["workflow_git_repo_path"].format(git_repo_path, MESSAGES["info_cli_from_arg"] if args.folder is not None else MESSAGES["info_cli_from_config"]), level='normal')
    log(MESSAGES["workflow_branch"].format(branch, MESSAGES["info_cli_from_arg"] if args.branch is not None else MESSAGES["info_cli_from_config_default"].format("main")), level='normal')
    log(MESSAGES["workflow_origin"].format(origin if origin else 'Not specified', MESSAGES["info_cli_from_arg"] if args.origin is not None else MESSAGES["info_cli_from_config_default"].format('Not specified')), level='normal')
    
    if command_line:
        log(MESSAGES["workflow_pre_commit_command"].format(command_line), level='normal')
    else:
        log(MESSAGES["workflow_no_pre_commit_command"], level='normal')
    
    log(MESSAGES["workflow_commit_message"].format(git_commit_message), level='normal')

    # --- 2. Initialize repository if necessary ---
    if not is_git_repo(git_repo_path, task_name):
        log(MESSAGES["workflow_repo_not_found_init_attempt"].format(git_repo_path), level='warning', task_name=task_name)
        if args.initialize:
            if not init_repo(git_repo_path, task_name):
                log(MESSAGES["workflow_repo_init_failed"].format(task_name), level='error', task_name=task_name)
                log(MESSAGES["workflow_task_aborted_repo_setup"].format(task_name), level='error', task_name=task_name)
                return False
            else:
                log(MESSAGES["workflow_repo_init_success"], level='success', task_name=task_name)
                if origin and not add_remote(git_repo_path, origin, task_name):
                    log(MESSAGES["workflow_task_aborted_repo_setup"].format(task_name), level='error', task_name=task_name)
                    return False
        else:
            log(MESSAGES["workflow_error_repo_not_valid"].format(git_repo_path, task_name), level='error', task_name=task_name)
            log(MESSAGES["workflow_hint_use_initialize"], level='info', task_name=task_name)
            log(MESSAGES["workflow_task_aborted_repo_setup"].format(task_name), level='error', task_name=task_name)
            return False
    else:
        log(MESSAGES["workflow_repo_found"].format(git_repo_path), level='normal', task_name=task_name)

    # --- 3. Checkout/create branch ---
    if not checkout_or_create_branch(git_repo_path, branch, origin, task_name):
        log(MESSAGES["workflow_task_aborted_repo_setup"].format(task_name), level='error', task_name=task_name)
        return False

    # --- 4. Initial Pull (always a good idea before operations) ---
    log(MESSAGES["workflow_initial_pull"], level='step', task_name=task_name)
    if not pull_updates(git_repo_path, "origin", branch, task_name):
        log(MESSAGES["workflow_initial_pull_failed"].format(task_name), level='error', task_name=task_name)
        return False
    log(MESSAGES["workflow_initial_pull_success"], level='success', task_name=task_name)

    # --- 5. Execute pre-commit command (if any) ---
    if command_line:
        log(MESSAGES["workflow_executing_command_line"], level='step', task_name=task_name)
        if execute_command(command_line, task_name, cwd=git_repo_path):
            log(MESSAGES["workflow_command_execution_success"], level='success', task_name=task_name)
        else:
            log(MESSAGES["workflow_command_execution_failed"].format(task_name), level='error', task_name=task_name)
            return False # Abort if pre-commit command fails
    else:
        log(MESSAGES["workflow_no_command_line"], level='normal', task_name=task_name)

    # --- 6. Check for changes, commit, and push ---
    log(MESSAGES["workflow_checking_for_changes"], level='step', task_name=task_name)
    has_changes, error_checking = check_for_changes(git_repo_path, task_name)
    if error_checking:
        log(MESSAGES["workflow_error_diff_check_failed"].format(task_name), level='error', task_name=task_name)
        return False

    if has_changes:
        log(MESSAGES["workflow_changes_detected_add_commit"], level='normal', task_name=task_name)
        if not git_add_commit(git_repo_path, git_commit_message, task_name):
            log(MESSAGES["workflow_git_add_commit_failed"].format(task_name), level='error', task_name=task_name)
            return False
        log(MESSAGES["workflow_git_add_commit_success"], level='success', task_name=task_name)

        log(MESSAGES["workflow_commits_made_push"], level='normal', task_name=task_name)
        if not git_push(git_repo_path, "origin", branch, task_name):
            log(MESSAGES["workflow_git_push_failed_warning"].format(task_name), level='warning', task_name=task_name)
            # Do not return False here, allow final pull even if push failed
        log(MESSAGES["workflow_git_push_success"], level='success', task_name=task_name)
    else:
        log(MESSAGES["workflow_no_changes_skip_commit"], level='normal', task_name=task_name)
        log(MESSAGES["workflow_no_commits_skip_push"], level='normal', task_name=task_name)

    # --- 7. Final Pull (post-push sync) ---
    log(MESSAGES["workflow_final_pull"], level='step', task_name=task_name)
    if not pull_updates(git_repo_path, "origin", branch, task_name):
        log(MESSAGES["workflow_final_pull_failed_warning"].format(task_name), level='warning', task_name=task_name)
    log(MESSAGES["workflow_final_pull_success"], level='success', task_name=task_name)
    
    log(MESSAGES["workflow_task_completed_success"].format(task_name), level='success', task_name=task_name)
    return True

def run_update_task_workflow(args, task, config_file_path):
    """
    Runs a streamlined update workflow: stash, pull, pop stash, commit, push, final pull.
    The pre-commit command is explicitly skipped when using this workflow.
    
    Args:
        args (argparse.Namespace): The parsed command-line arguments.
        task (dict): The task configuration loaded from the JSON file.
        config_file_path (str): The path to the task's configuration file.
    """
    task_name = task.get("name", "Unnamed Task")
    log(MESSAGES["workflow_start_update_task"].format(task_name), level='step', task_name=task_name)

    # --- 1. Get and confirm configuration values (with overrides) ---
    git_repo_path = args.folder if args.folder is not None else task.get("git_repo_path")
    branch = args.branch if args.branch is not None else task.get("branch", "main")
    origin = args.origin if args.origin is not None else task.get("origin")
    # When --update is used, explicitly disable the command_line
    command_line = "" # This makes sure the pre-commit command is NOT run
    git_commit_message = task.get("git_commit_message", f"Automated update for {task_name}")

    if not git_repo_path:
        log(MESSAGES["workflow_error_missing_repo_path"].format(task_name), level='error', task_name=task_name)
        log(MESSAGES["workflow_task_aborted_missing_info"].format(task_name), level='error', task_name=task_name)
        return False

    log(MESSAGES["workflow_task_details"].format(task_name), level='normal')
    log(MESSAGES["workflow_git_repo_path"].format(git_repo_path, MESSAGES["info_cli_from_arg"] if args.folder is not None else MESSAGES["info_cli_from_config"]), level='normal')
    log(MESSAGES["workflow_branch"].format(branch, MESSAGES["info_cli_from_arg"] if args.branch is not None else MESSAGES["info_cli_from_config_default"].format("main")), level='normal')
    log(MESSAGES["workflow_origin"].format(origin if origin else 'Not specified', MESSAGES["info_cli_from_arg"] if args.origin is not None else MESSAGES["info_cli_from_config_default"].format('Not specified')), level='normal')
    
    # Message reflecting that the command is skipped for update workflow
    log(MESSAGES["workflow_no_pre_commit_command"], level='info', task_name=task_name)
    
    log(MESSAGES["workflow_commit_message"].format(git_commit_message), level='normal')

    # --- 2. Validate repository ---
    if not is_git_repo(git_repo_path, task_name):
        log(MESSAGES["workflow_error_repo_not_valid_update"].format(git_repo_path, task_name), level='error', task_name=task_name)
        log(MESSAGES["workflow_task_aborted_repo_setup"].format(task_name), level='error', task_name=task_name)
        return False
    else:
        log(MESSAGES["workflow_repo_found"].format(git_repo_path), level='normal', task_name=task_name)

    # --- 3. Checkout/create branch ---
    if not checkout_or_create_branch(git_repo_path, branch, origin, task_name):
        log(MESSAGES["workflow_task_aborted_repo_setup"].format(task_name), level='error', task_name=task_name)
        return False

    # --- 4. Stash local changes before pulling ---
    log(MESSAGES["git_checking_local_changes_for_stash"], level='normal', task_name=task_name)
    has_changes, error_checking = check_for_changes(git_repo_path, task_name)
    if error_checking:
        log(MESSAGES["workflow_error_diff_check_failed"].format(task_name), level='error', task_name=task_name)
        return False

    stashed = False
    if has_changes:
        log(MESSAGES["git_changes_found_stashing"], level='normal', task_name=task_name)
        if not stash_local_changes(git_repo_path, task_name):
            log(MESSAGES["git_stash_failed"].format(task_name), level='error', task_name=task_name)
            return False
        stashed = True
    else:
        log(MESSAGES["git_no_changes_to_stash"], level='normal', task_name=task_name)

    # --- 5. Pull updates ---
    log(MESSAGES["workflow_pre_commit_pull"], level='step', task_name=task_name)
    if not pull_updates(git_repo_path, "origin", branch, task_name):
        log(MESSAGES["workflow_pre_commit_pull_failed"].format(task_name), level='error', task_name=task_name)
        if stashed:
            # Attempt to pop stash even if pull failed, to restore state
            log(MESSAGES["git_stash_pop_applying"], level='info', task_name=task_name)
            pop_stashed_changes(git_repo_path, task_name) # Logged internally
        log(MESSAGES["workflow_update_aborted_pull_failed"].format(task_name), level='error', task_name=task_name)
        return False
    log(MESSAGES["workflow_pre_commit_pull_success"], level='success', task_name=task_name)

    # --- 6. Pop stashed changes (if any) ---
    if stashed:
        log(MESSAGES["git_stash_pop_applying"], level='step', task_name=task_name)
        if not pop_stashed_changes(git_repo_path, task_name):
            # If pop fails, warn but try to continue to commit remaining changes
            log(MESSAGES["git_stash_pop_failed_conflict"], level='warning', task_name=task_name)
            # The user will need to resolve conflicts manually

    # --- 7. Pre-commit command is explicitly skipped for --update workflow
    log(MESSAGES["workflow_no_command_line"], level='normal', task_name=task_name) # Reinforce that it's skipped

    # --- 8. Check for changes, commit, and push ---
    log(MESSAGES["workflow_checking_for_changes"], level='step', task_name=task_name)
    has_changes, error_checking = check_for_changes(git_repo_path, task_name)
    if error_checking:
        log(MESSAGES["workflow_error_diff_check_failed"].format(task_name), level='error', task_name=task_name)
        return False

    if has_changes:
        log(MESSAGES["workflow_changes_detected_add_commit"], level='normal', task_name=task_name)
        if not git_add_commit(git_repo_path, git_commit_message, task_name):
            log(MESSAGES["workflow_git_add_commit_failed"].format(task_name), level='error', task_name=task_name)
            return False
        log(MESSAGES["workflow_git_add_commit_success"], level='success', task_name=task_name)

        log(MESSAGES["workflow_commits_made_push"], level='normal', task_name=task_name)
        if not git_push(git_repo_path, "origin", branch, task_name):
            log(MESSAGES["workflow_git_push_failed_warning"].format(task_name), level='warning', task_name=task_name)
            # Do not return False here, allow final pull even if push failed
        log(MESSAGES["workflow_git_push_success"], level='success', task_name=task_name)
    else:
        log(MESSAGES["workflow_no_changes_skip_commit"], level='normal', task_name=task_name)
        log(MESSAGES["workflow_no_commits_skip_push"], level='normal', task_name=task_name)

    # --- 9. Final Pull (post-push sync) ---
    log(MESSAGES["workflow_final_pull"], level='step', task_name=task_name)
    if not pull_updates(git_repo_path, "origin", branch, task_name):
        log(MESSAGES["workflow_final_pull_failed_warning"].format(task_name), level='warning', task_name=task_name)
    log(MESSAGES["workflow_final_pull_success"], level='success', task_name=task_name)
    
    log(MESSAGES["workflow_task_completed_success"].format(task_name), level='success', task_name=task_name)
    return True