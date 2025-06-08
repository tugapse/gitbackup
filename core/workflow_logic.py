# core/workflow_logic.py

import os
import sys
from datetime import datetime
from core.logger import log
from core.command_logic import execute_command
from core.messages import MESSAGES

from core.git_logic import (
    initialize_repo,
    checkout_or_create_branch,
    pull_updates,
    diff_changes,
    add_commit_changes,
    push_updates
)


def run_task_workflow(args, task, config_file_path):
    """
    Executes the full Git automation workflow for a given task.
    """
    log(MESSAGES["workflow_start_task"].format(config_file_path), level='step')

    task_name = task.get("name", "Unnamed Task")
    command_line = task.get("command_line", "")
    
    # RENAMED: Get default_commit_message and generate_commit_message_command
    default_commit_message = task.get("default_commit_message", f"Automated update for {task_name}")
    generate_commit_message_command = task.get("generate_commit_message_command", None)

    git_repo_path = args.folder if args.folder is not None else task.get("git_repo_path")
    branch = args.branch if args.branch is not None else task.get("branch", "main")
    origin = args.origin if args.origin is not None else task.get("origin", "origin")

    log(MESSAGES["workflow_task_details"].format(task_name), level='normal')
    log(MESSAGES["workflow_git_repo_path"].format(git_repo_path, MESSAGES["info_cli_from_arg"] if args.folder is not None else MESSAGES["info_cli_from_config"]), level='normal')
    log(MESSAGES["workflow_branch"].format(branch, MESSAGES["info_cli_from_arg"] if args.branch is not None else MESSAGES["info_cli_from_config_default"]), level='normal')
    log(MESSAGES["workflow_origin"].format(origin, MESSAGES["info_cli_from_arg"] if args.origin is not None else MESSAGES["info_cli_from_config_default"]), level='normal')
    if command_line:
        log(MESSAGES["workflow_precommit_command"].format(command_line), level='normal')
    else:
        log(MESSAGES["workflow_no_precommit_command"], level='normal')
    
    log(MESSAGES["workflow_default_commit_message"].format(default_commit_message), level='normal') # NEW LOG
    if generate_commit_message_command:
        log(MESSAGES["workflow_generate_commit_message_command"].format(generate_commit_message_command), level='normal') # NEW LOG
    else:
        log(MESSAGES["workflow_no_generate_commit_message_command"], level='normal') # NEW LOG


    # --- Pre-requisite checks & Initialization ---
    if not git_repo_path:
        log(MESSAGES["workflow_error_missing_repo_path"].format(task_name), level='error')
        log(MESSAGES["workflow_task_aborted_missing_info"].format(task_name), level='error')
        sys.exit(1)

    git_dir_exists = os.path.exists(os.path.join(git_repo_path, '.git'))
    
    if not git_dir_exists:
        if args.initialize:
            log(MESSAGES["workflow_repo_not_found_init_attempt"].format(git_repo_path), level='step', task_name=task_name)
            if not initialize_repo(git_repo_path, origin_url=origin, task_name=task_name):
                log(MESSAGES["workflow_repo_init_failed"].format(task_name), level='error')
                sys.exit(1)
            log(MESSAGES["workflow_repo_init_success"], level='success', task_name=task_name)
        else:
            log(MESSAGES["workflow_error_repo_not_valid"].format(task_name, git_repo_path), level='error')
            log(MESSAGES["workflow_hint_use_initialize"], level='error')
            log(MESSAGES["workflow_task_aborted_repo_setup"].format(task_name), level='error')
            sys.exit(1)
    else:
        log(MESSAGES["workflow_repo_found"].format(git_repo_path), level='normal', task_name=task_name)

    # --- Checkout or Create Branch ---
    if not checkout_or_create_branch(git_repo_path, branch, origin, task_name):
        log(MESSAGES["workflow_checkout_branch_failed"].format(task_name, branch), level='error')
        sys.exit(1)


    # --- Initial Git Pull ---
    log(MESSAGES["workflow_initial_pull"], level='step', task_name=task_name)
    if pull_updates(git_repo_path, branch, task_name):
        log(MESSAGES["workflow_initial_pull_success"], level='success', task_name=task_name)
    else:
        log(MESSAGES["workflow_initial_pull_failed"].format(task_name), level='error')
        sys.exit(1)


    # --- Execute Command Line ---
    log(MESSAGES["workflow_executing_command_line"], level='step', task_name=task_name)
    if command_line:
        if execute_command(command_line, task_name, cwd=git_repo_path):
            log(MESSAGES["workflow_command_execution_success"], level='success', task_name=task_name)
        else:
            log(MESSAGES["workflow_command_execution_failed"].format(task_name), level='error')
            sys.exit(1)
    else:
        log(MESSAGES["workflow_no_command_line"], level='normal', task_name=task_name)


    # --- Determine the final commit message ---
    final_commit_base_message = default_commit_message
    if generate_commit_message_command:
        log(MESSAGES["git_executing_generate_message_command"].format(generate_commit_message_command), level='normal', task_name=task_name)
        # Assuming execute_command can return output if capture_output is implicitly true for it.
        # It needs to return (stdout, success) tuple.
        cmd_output, cmd_success = execute_command(generate_commit_message_command, task_name, cwd=git_repo_path, capture_output=True)
        if cmd_success and cmd_output.strip():
            final_commit_base_message = cmd_output.strip()
        else:
            log(MESSAGES["git_generate_message_command_failed"], level='warning', task_name=task_name)
            # Retain default_commit_message if command failed or returned empty

    # The timestamp appending logic remains the same (it's in add_commit_changes)
    # The actual timestamp is appended in core/git_logic.py::add_commit_changes


    # --- Check for Changes & Commit ---
    log(MESSAGES["workflow_checking_for_changes"], level='step', task_name=task_name)
    changes_found = diff_changes(git_repo_path, task_name)
    
    if changes_found is None:
        log(MESSAGES["workflow_error_diff_check_failed"].format(task_name), level='error')
        sys.exit(1)
    elif changes_found:
        log(MESSAGES["workflow_changes_detected_add_commit"], level='step', task_name=task_name)
        # Pass the dynamically determined base message to add_commit_changes
        if add_commit_changes(git_repo_path, final_commit_base_message, ".", task_name):
            log(MESSAGES["workflow_git_add_commit_success"], level='success', task_name=task_name)
            commit_successful = True
        else:
            log(MESSAGES["workflow_git_add_commit_failed"].format(task_name), level='error')
            sys.exit(1)
    else:
        log(MESSAGES["workflow_no_changes_skip_commit"], level='normal', task_name=task_name)
        commit_successful = False


    # --- Git Push ---
    if commit_successful:
        log(MESSAGES["workflow_commits_made_push"], level='step', task_name=task_name)
        if push_updates(git_repo_path, branch, origin, task_name):
            log(MESSAGES["workflow_git_push_success"], level='success', task_name=task_name)
        else:
            log(MESSAGES["workflow_git_push_failed_warning"].format(task_name), level='error')
    else:
        log(MESSAGES["workflow_no_commits_skip_push"], level='normal', task_name=task_name)


    # --- Final Git Pull (Post-push sync) ---
    log(MESSAGES["workflow_final_pull"], level='step', task_name=task_name)
    if pull_updates(git_repo_path, branch, task_name):
        log(MESSAGES["workflow_final_pull_success"], level='success', task_name=task_name)
    else:
        log(MESSAGES["workflow_final_pull_failed_warning"].format(task_name), level='error')


    log(MESSAGES["workflow_task_completed_success"].format(task_name), level='success', task_name=task_name)

