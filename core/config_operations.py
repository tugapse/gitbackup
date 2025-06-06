# core/config_operations.py

import os
import json
import subprocess
import sys
from types import SimpleNamespace # Used to convert dict to object for easier access

from core.logger import log # Import log function
from core.messages import MESSAGES # Import messages for consistent logging

def get_default_config_dir(custom_dir=None):
    """
    Determines the default configuration directory based on OS,
    or uses a custom directory if provided.
    """
    if custom_dir:
        return custom_dir

    if os.name == 'posix': # Linux, macOS, etc.
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config_home:
            return os.path.join(xdg_config_home, 'git_automation_configs')
        else:
            return os.path.join(os.path.expanduser("~"), '.config', 'git_automation_configs')
    elif os.name == 'nt': # Windows
        appdata = os.environ.get('APPDATA')
        if appdata:
            return os.path.join(appdata, 'git_automation_configs')
        else:
            # Fallback for Windows if APPDATA is not set (unlikely)
            return os.path.join(os.path.expanduser("~"), 'AppData', 'Roaming', 'git_automation_configs')
    else:
        log(MESSAGES["config_warning_unknown_os"], level='warning')
        return os.getcwd() # Fallback to current working directory

def get_config_file_path(task_identifier, config_dir):
    """Constructs the full path to a task's configuration file."""
    if not config_dir:
        log(MESSAGES["config_error_no_config_dir"], level='error')
        return None
    return os.path.join(config_dir, f"{task_identifier}.json")

def create_config_file(args):
    """Creates a new task configuration file."""
    config_dir = args.config_dir
    task_identifier = args.task_identifier
    config_file_path = get_config_file_path(task_identifier, config_dir)

    if not config_file_path:
        return # Error already logged

    os.makedirs(config_dir, exist_ok=True)

    if os.path.exists(config_file_path) and not args.overwrite:
        log(MESSAGES["config_error_file_exists"].format(config_file_path), level='error')
        log(MESSAGES["config_use_overwrite_option"], level='info')
        return

    # Default configuration structure
    default_config = {
        "name": task_identifier,
        "folder": "/path/to/your/repository", # Placeholder
        "branch": "main",
        "origin": "https://github.com/user/repo.git",
        "pull_before_command": True,
        "pre_command": "",
        "commit_message": f"Automated update for {task_identifier}",
        "push_after_command": True,
        "post_command": "",
        "timestamp_format": "%Y-%m-%d %H:%M:%S" # NEW KEY ADDED HERE
    }

    # Apply command-line overrides for new config
    if args.folder:
        default_config["folder"] = args.folder
    if args.branch:
        default_config["branch"] = args.branch
    if args.origin:
        default_config["origin"] = args.origin

    try:
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        log(MESSAGES["config_created_successfully"].format(config_file_path), level='success')
        log(MESSAGES["config_edit_recommendation"].format(task_identifier, task_identifier), level='info')
    except IOError as e:
        log(MESSAGES["config_error_creating_file"].format(config_file_path, e), level='error')

def edit_config_file(args):
    """Opens a task configuration file for editing."""
    config_dir = args.config_dir
    task_identifier = args.task_identifier
    config_file_path = get_config_file_path(task_identifier, config_dir)

    if not config_file_path:
        return # Error already logged

    if not os.path.exists(config_file_path):
        log(MESSAGES["config_error_edit_file_not_found"].format(task_identifier), level='error')
        log(MESSAGES["config_create_recommendation"].format(task_identifier), level='info')
        return

    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'nano' # Fallback to nano

    log(MESSAGES["config_opened_for_editing"].format(config_file_path), level='info')
    try:
        subprocess.run([editor, config_file_path], check=True)
    except FileNotFoundError:
        log(MESSAGES["config_error_editor_not_found"].format(editor), level='error')
    except subprocess.CalledProcessError as e:
        log(MESSAGES["config_error_editor_exit"].format(editor, e.returncode), level='error')
    except Exception as e:
        log(MESSAGES["config_error_editing_file"].format(config_file_path, e), level='error')

def list_tasks(args):
    """Lists all available task configuration files."""
    config_dir = args.config_dir

    if not config_dir or not os.path.isdir(config_dir):
        log(MESSAGES["config_no_config_dir_found"].format(config_dir), level='warning')
        return

    config_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]

    if not config_files:
        log(MESSAGES["config_no_tasks_found"], level='info')
        return

    log(MESSAGES["config_listing_tasks"].format(config_dir), level='info')
    for f in sorted(config_files):
        log(f"- {os.path.splitext(f)[0]}", level='normal') # Print task identifier without .json

def read_config_file(file_path):
    """Reads and parses a JSON configuration file."""
    if not os.path.exists(file_path):
        log(MESSAGES["config_error_file_not_found"].format(file_path), level='error')
        return None

    log(MESSAGES["config_reading_file"].format(file_path), level='info')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Convert dictionary to SimpleNamespace for attribute-like access
        task = SimpleNamespace(**config_data)

        # Ensure required fields exist. Add defaults if missing.
        if not hasattr(task, 'name') or not task.name:
            task.name = os.path.splitext(os.path.basename(file_path))[0]
            log(f"Config '{file_path}' missing 'name' field, defaulting to filename: '{task.name}'", level='warning')
        if not hasattr(task, 'folder') or not task.folder:
            log(f"Config '{file_path}' missing 'folder' field. This task may not run correctly.", level='error')
            return None # Folder is critical, so return None
        if not hasattr(task, 'branch') or not task.branch:
            log(f"Config '{file_path}' missing 'branch' field, defaulting to 'main'.", level='warning')
            task.branch = "main"
        if not hasattr(task, 'origin'): # Origin is optional, but ensure attribute exists
            task.origin = ""
        if not hasattr(task, 'pull_before_command'):
            task.pull_before_command = True
        if not hasattr(task, 'pre_command'):
            task.pre_command = ""
        if not hasattr(task, 'commit_message') or not task.commit_message:
            log(f"Config '{file_path}' missing 'commit_message' field, defaulting to 'Automated commit for {task.name}'.", level='warning')
            task.commit_message = f"Automated commit for {task.name}"
        if not hasattr(task, 'push_after_command'):
            task.push_after_command = True
        if not hasattr(task, 'post_command'):
            task.post_command = ""
        # NEW: Ensure timestamp_format exists with a default if not present
        if not hasattr(task, 'timestamp_format'):
            task.timestamp_format = "%Y-%m-%d %H:%M:%S"
            log(f"Config '{file_path}' missing 'timestamp_format' field, defaulting to '{task.timestamp_format}'.", level='warning')


        return task
    except json.JSONDecodeError as e:
        log(MESSAGES["config_error_invalid_json"].format(file_path, e), level='error')
        return None
    except Exception as e:
        log(MESSAGES["config_error_reading_file"].format(file_path, e), level='error')
        return None