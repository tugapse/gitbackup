# core/config_operations.py

import json
import os
import subprocess
import sys
from core.logger import log
from core.messages import MESSAGES

DEFAULT_CONFIG_DIR_NAME = "git_automation_configs"

def get_default_config_dir(args_config_dir=None):
    """
    Determines the default configuration directory based on XDG Base Directory Specification
    or a fallback for Windows, prioritizing the CLI argument if provided.
    """
    if args_config_dir:
        return args_config_dir

    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config_home:
        return os.path.join(xdg_config_home, DEFAULT_CONFIG_DIR_NAME)
    else:
        # Fallback for systems not using XDG_CONFIG_HOME or for Windows
        if os.name == 'posix': # Linux, macOS, etc.
            home_dir = os.path.expanduser("~")
            return os.path.join(home_dir, '.config', DEFAULT_CONFIG_DIR_NAME)
        elif os.name == 'nt': # Windows
            appdata = os.environ.get('APPDATA')
            return os.path.join(appdata, DEFAULT_CONFIG_DIR_NAME)
        else:
            # Generic fallback if OS not recognized
            return os.path.join(os.getcwd(), DEFAULT_CONFIG_DIR_NAME)

def get_config_file_path(task_identifier, config_dir=None):
    """
    Determines the full path to a configuration file.
    It checks if task_identifier is already a path, otherwise constructs it.
    """
    if os.path.isabs(task_identifier) and task_identifier.endswith('.json'):
        return task_identifier
    if config_dir is None:
        config_dir = get_default_config_dir()
    return os.path.join(config_dir, f"{task_identifier}.json")

def create_config_file(args):
    """Creates a new JSON configuration file for a task."""
    task_name = args.task_identifier
    output_path = args.output if args.output else get_config_file_path(task_name, args.config_dir)

    if os.path.exists(output_path) and not args.overwrite:
        log(MESSAGES["config_file_exists_no_overwrite"].format(output_path), level='error')
        return

    log(MESSAGES["config_creation_prompt_repo_path"], level='normal', task_name=task_name)
    git_repo_path = input()

    log(MESSAGES["config_creation_prompt_branch"].format("main"), level='normal', task_name=task_name)
    branch = input() or "main"

    log(MESSAGES["config_creation_prompt_origin"], level='normal', task_name=task_name)
    origin = input()

    log(MESSAGES["config_creation_prompt_command"], level='normal', task_name=task_name)
    command_line = input()

    log(MESSAGES["config_creation_prompt_commit_msg"].format(task_name), level='normal', task_name=task_name)
    git_commit_message = input() or f"Automated update for {task_name}"

    config_data = {
        "name": task_name,
        "git_repo_path": git_repo_path,
        "branch": branch,
        "origin": origin,
        "command_line": command_line,
        "git_commit_message": git_commit_message
    }

    config_dir = os.path.dirname(output_path)
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir)
            log(MESSAGES["config_default_config_path_created"].format(config_dir), level='normal', task_name=task_name)
        except OSError as e:
            log(MESSAGES["config_error_creating_default_config_path"].format(config_dir, e), level='error', task_name=task_name)
            return

    try:
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        log(MESSAGES["config_file_created_success"].format(task_name, output_path), level='success', task_name=task_name)
    except IOError as e:
        log(MESSAGES["config_file_creation_failed"].format(task_name, e), level='error', task_name=task_name)

def read_config_file(file_path):
    """Reads and parses a JSON configuration file."""
    if not os.path.exists(file_path):
        log(MESSAGES["cli_error_config_file_not_found"].format(file_path), level='error')
        return None
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        if not isinstance(config, dict):
            log(MESSAGES["cli_error_json_not_object"].format(file_path), level='error')
            return None
        return config
    except json.JSONDecodeError as e:
        log(MESSAGES["cli_error_invalid_json_format"].format(file_path, e), level='error')
        return None
    except Exception as e:
        log(MESSAGES["cli_error_unexpected_reading_config"].format(file_path, e), level='error')
        return None

def edit_config_file(args):
    """Opens a configuration file in the default text editor."""
    task_identifier = args.task_identifier
    json_path = args.json

    if not task_identifier and not json_path:
        log(MESSAGES["cli_error_edit_no_args"], level='error')
        log(MESSAGES["cli_edit_usage_hint"], level='info')
        return

    file_to_edit = json_path if json_path else get_config_file_path(task_identifier, args.config_dir)

    log(MESSAGES["cli_attempting_open_editor"].format(file_to_edit), level='normal')

    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL')
    if not editor:
        if sys.platform.startswith('linux') or sys.platform == 'darwin':
            editor = 'xdg-open' if sys.platform.startswith('linux') else 'open'
        elif sys.platform == 'win32':
            editor = 'notepad' # Fallback for Windows

    if not editor:
        log(MESSAGES["cli_error_editor_not_found"].format(sys.platform), level='error')
        return

    try:
        if sys.platform.startswith('linux') and editor == 'xdg-open':
            subprocess.Popen([editor, file_to_edit])
        elif sys.platform == 'darwin' and editor == 'open':
            subprocess.Popen([editor, file_to_edit])
        elif sys.platform == 'win32' and editor == 'notepad':
            subprocess.Popen([editor, file_to_edit])
        else: # Generic fallback for other editors
            subprocess.Popen([editor, file_to_edit])

        log(MESSAGES["cli_editor_launched_success"].format(file_to_edit), level='success')
    except FileNotFoundError:
        log(MESSAGES["cli_error_editor_not_found"].format(editor), level='error')
    except Exception as e:
        log(MESSAGES["cli_error_opening_file_editor"].format(e), level='error')
        log(MESSAGES["cli_error_unexpected_opening_file"].format(e), level='error')


def list_tasks(args):
    """Lists all available task configuration files in the specified directory."""
    config_dir = get_default_config_dir(args.config_dir)
    log(MESSAGES["cli_listing_tasks_in"].format(config_dir), level='normal')

    if not os.path.exists(config_dir) or not os.path.isdir(config_dir):
        log(MESSAGES["cli_no_config_files_found"].format(config_dir), level='info')
        return

    json_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]

    if not json_files:
        log(MESSAGES["cli_no_config_files_found"].format(config_dir), level='info')
        return

    found_tasks = []
    for filename in json_files:
        file_path = os.path.join(config_dir, filename)
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
                if isinstance(config, dict) and "name" in config:
                    found_tasks.append((config["name"], file_path))
                else:
                    log(MESSAGES["cli_warning_malformed_json"].format(filename), level='warning')
        except json.JSONDecodeError:
            log(MESSAGES["cli_warning_malformed_json"].format(filename), level='warning')
        except Exception as e:
            log(MESSAGES["cli_warning_unexpected_error_reading_file"].format(filename, e), level='warning')

    if found_tasks:
        for task_name, file_path in sorted(found_tasks):
            log(MESSAGES["workflow_task_details"].format(f"{task_name} (File: {file_path})"), level='normal')
    else:
        log(MESSAGES["cli_no_valid_configs_found"].format(config_dir), level='info')