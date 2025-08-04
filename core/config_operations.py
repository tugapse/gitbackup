# core/config_operations.py

import os
import json
import sys
from core.logger import log
from core.messages import MESSAGES

# Define the default structure for a task configuration
DEFAULT_TASK_CONFIG = {
    "name": "default-task",
    "origin": "origin",
    "branch": "main",
    "git_repo_path": os.path.abspath(os.path.join(os.getcwd(), "path/to/your/local_git_repo")),
    "command_line": "echo 'Your command here (e.g., npm run build, python script.py)'",
    "default_commit_message": "Automated update",
    "generate_commit_message_command": None,
    "handle_local_changes_before_pull": "auto_stash" # NEW FIELD: default to auto_stash
}


def create_config_file(name, output_filepath, branch_arg=None, origin_arg=None, folder_arg=None, overwrite_flag=False):
    """
    Creates a new JSON configuration file with default values and optional
    branch/origin/folder from CLI arguments.
    Ensures the directory path exists and handles overwrite logic.
    """
    log(MESSAGES["config_start_creation"].format(name), level='step')
    log(MESSAGES["config_target_output_path"].format(output_filepath), level='normal')

    # Start with a copy of the default config
    new_config = DEFAULT_TASK_CONFIG.copy()
    new_config["name"] = name
    
    # Apply arguments if provided
    if origin_arg is not None:
        new_config["origin"] = origin_arg
    if branch_arg is not None:
        new_config["branch"] = branch_arg
    if folder_arg is not None:
        new_config["git_repo_path"] = folder_arg
    
    # Update default_commit_message based on the new name
    new_config["default_commit_message"] = f"Automated update for {name}"


    if not output_filepath.lower().endswith(".json"):
        output_filepath += ".json"
        log(MESSAGES["config_appended_json_extension"].format(output_filepath), level='normal')

    if os.path.exists(output_filepath):
        if not overwrite_flag:
            log(MESSAGES["config_file_exists_error"].format(output_filepath), level='error')
            sys.exit(1)
        else:
            log(MESSAGES["config_file_exists_warning_overwrite"].format(output_filepath), level='normal')

    output_dir = os.path.dirname(output_filepath)
    if output_dir and not os.path.exists(output_dir):
        log(MESSAGES["config_parent_dir_not_exist"].format(output_dir), level='normal')
        try:
            os.makedirs(output_dir, exist_ok=True)
            log(MESSAGES["config_dir_created_success"].format(output_dir), level='normal')
        except Exception as e:
            log(MESSAGES["config_error_creating_dir"].format(output_dir, e), level='error')
            sys.exit(1)
    elif not output_dir:
        output_dir = os.getcwd()
        log(MESSAGES["config_output_to_cwd"].format(output_dir), level='normal')
    else:
        log(MESSAGES["config_parent_dir_exists"].format(output_dir), level='normal')

    try:
        with open(output_filepath, 'w') as f:
            json.dump(new_config, f, indent=2) # Dump the prepared new_config
        log(MESSAGES["config_creation_success"].format(output_filepath), level='success')
        log(MESSAGES["config_edit_hint"], level='normal')
    except Exception as e:
        log(MESSAGES["config_creation_failed"].format(output_filepath, e), level='error')
        sys.exit(1)

    log(MESSAGES["config_finished_creation"].format(name), level='step')


def fix_config_files(config_dir):
    """
    Iterates through all JSON files in the config_dir and adds any missing keys
    from the DEFAULT_TASK_CONFIG.
    """
    log(MESSAGES["config_start_fixing_jsons"].format(config_dir), level='step')

    if not os.path.isdir(config_dir):
        log(MESSAGES["cli_no_config_files_found"].format(config_dir), level='info')
        return

    for filename in os.listdir(config_dir):
        if filename.lower().endswith(".json"):
            filepath = os.path.join(config_dir, filename)
            log(MESSAGES["config_fixing_file"].format(filename), level='normal')
            
            try:
                with open(filepath, 'r') as f:
                    current_config = json.load(f)
                
                if not isinstance(current_config, dict):
                    log(MESSAGES["config_fixed_skipped_malformed"].format(filename), level='warning')
                    continue

                updated = False
                for key, default_value in DEFAULT_TASK_CONFIG.items():
                    if key not in current_config:
                        current_config[key] = default_value
                        updated = True
                
                if updated:
                    with open(filepath, 'w') as f:
                        json.dump(current_config, f, indent=2)
                    log(MESSAGES["config_fixed_success"].format(filename), level='success')
                else:
                    log(MESSAGES["config_file_up_to_date"].format(filename), level='normal')

            except json.JSONDecodeError:
                log(MESSAGES["config_fixed_skipped_malformed"].format(filename), level='warning')
            except Exception as e:
                log(MESSAGES["config_fixed_error"].format(filename, e), level='error')
    
    log(MESSAGES["config_finished_fixing_jsons"], level='step')


def load_task_config(filepath):
    """
    Loads a JSON task configuration from the given filepath.
    Handles file not found, JSON decode errors, and non-dict JSONs.
    Exits the script on error.
    """
    if not os.path.exists(filepath):
        log(MESSAGES["cli_error_config_file_not_found"].format(filepath), level='error')
        sys.exit(1)
    
    try:
        with open(filepath, 'r') as f:
            task = json.load(f)
    except json.JSONDecodeError as e:
        log(MESSAGES["cli_error_invalid_json_format"].format(filepath, e), level='error')
        sys.exit(1)
    except Exception as e:
        log(MESSAGES["cli_error_unexpected_reading_config"].format(filepath, e), level='error')
        sys.exit(1)

    if not isinstance(task, dict):
        log(MESSAGES["cli_error_json_not_object"].format(filepath), level='error')
        sys.exit(1)
    
    return task