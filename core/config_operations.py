import json
import os
import sys
import subprocess
from types import SimpleNamespace # Import SimpleNamespace here

from core.logger import log
from core.messages import MESSAGES

def get_default_config_dir(args_config_dir=None):
    """
    Determines the default configuration directory based on XDG Base Directory Specification
    or OS-specific conventions, allowing override via CLI arg or env var.
    """
    if args_config_dir:
        return args_config_dir

    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config_home:
        return os.path.join(xdg_config_home, 'git_automation_configs')
    else:
        if os.name == 'posix': # Linux, macOS, etc.
            home_dir = os.path.expanduser("~")
            return os.path.join(home_dir, '.config', 'git_automation_configs')
        elif os.name == 'nt': # Windows
            appdata = os.environ.get('APPDATA')
            return os.path.join(appdata, 'git_automation_configs')
        else:
            log(MESSAGES["config_warning_unknown_os"], level='warning')
            return os.path.join(os.getcwd(), 'git_automation_configs')

def get_config_file_path(task_identifier, config_dir):
    """Constructs the full path to a task configuration file."""
    if not config_dir:
        log(MESSAGES["config_error_no_config_dir"], level='error')
        return None
    return os.path.join(config_dir, f"{task_identifier}.json")

def create_config_file(args):
    """
    Creates a new task configuration file with default or specified values.
    """
    task_name = args.task_identifier
    config_dir = get_default_config_dir(args.config_dir)
    file_path = get_config_file_path(task_name, config_dir)

    if os.path.exists(file_path) and not args.overwrite:
        log(MESSAGES["config_error_file_exists"].format(file_path), level='error')
        log(MESSAGES["config_use_overwrite_option"], level='info')
        return

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # This defines the expected structure for config files
    # These keys MUST match the attributes accessed in workflow_logic.py
    default_config = {
        "name": task_name,
        "folder": os.path.join(os.path.expanduser("~"), task_name),
        "branch": "main",
        "origin": "",
        "pull_before_command": True,
        "pre_command": "",
        "commit_message": f"Automated update for {task_name}",
        "push_after_command": True,
        "post_command": ""
    }

    # Apply overrides from CLI arguments if provided
    if args.folder:
        default_config["folder"] = args.folder
    if args.branch:
        default_config["branch"] = args.branch
    if args.origin:
        default_config["origin"] = args.origin

    try:
        with open(file_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        log(MESSAGES["config_created_successfully"].format(file_path), level='success')
        log(MESSAGES["config_edit_recommendation"].format(task_name), level='info')
    except IOError as e:
        log(MESSAGES["config_error_creating_file"].format(file_path, e), level='error')

def edit_config_file(args):
    """
    Opens a task configuration file for editing.
    """
    task_identifier = args.task_identifier
    config_dir = get_default_config_dir(args.config_dir)
    file_path = get_config_file_path(task_identifier, config_dir)

    if not os.path.exists(file_path):
        log(MESSAGES["config_error_edit_file_not_found"].format(file_path), level='error')
        log(MESSAGES["config_create_recommendation"].format(task_identifier), level='info')
        return

    editor = os.environ.get('EDITOR', os.environ.get('VISUAL', 'nano')) # Fallback to nano

    try:
        subprocess.run([editor, file_path], check=True)
        log(MESSAGES["config_opened_for_editing"].format(file_path), level='success')
    except FileNotFoundError:
        log(MESSAGES["config_error_editor_not_found"].format(editor), level='error')
    except subprocess.CalledProcessError as e:
        log(MESSAGES["config_error_editor_exit"].format(editor, e), level='error')
    except Exception as e:
        log(MESSAGES["config_error_editing_file"].format(file_path, e), level='error')

def list_tasks(args):
    """
    Lists all available task configuration files.
    """
    config_dir = get_default_config_dir(args.config_dir)
    
    if not os.path.isdir(config_dir):
        log(MESSAGES["config_no_config_dir_found"].format(config_dir), level='warning')
        return

    log(MESSAGES["config_listing_tasks"].format(config_dir), level='normal')
    tasks = [f for f in os.listdir(config_dir) if f.endswith('.json')]
    
    if not tasks:
        log(MESSAGES["config_no_tasks_found"], level='info')
        return

    for task_file in sorted(tasks):
        task_name = os.path.splitext(task_file)[0]
        log(f"- {task_name}", level='normal')

def read_config_file(file_path):
    """
    Reads and parses a task configuration file.
    Returns a SimpleNamespace object representing the config, or None if an error occurs.
    """
    if not os.path.exists(file_path):
        log(MESSAGES["config_error_file_not_found"].format(file_path), level='error')
        return None

    log(MESSAGES["config_reading_file"].format(file_path), level='info')
    try:
        with open(file_path, 'r') as f:
            config_data = json.load(f)
            # Convert the dictionary to an object with attribute access
            # This requires the JSON keys to match the expected attributes (e.g., "folder", not "git_repo_path")
            return SimpleNamespace(**config_data)
    except json.JSONDecodeError as e:
        log(MESSAGES["config_error_invalid_json"].format(file_path, e), level='error')
        return None
    except Exception as e:
        log(MESSAGES["config_error_reading_file"].format(file_path, e), level='error')
        return None