# core/config_operations.py

import os
import json
import sys
from core.logger import log
from core.messages import MESSAGES

def create_config_file(name, output_filepath, branch_arg=None, origin_arg=None, folder_arg=None, overwrite_flag=False):
    """
    Creates a new JSON configuration file with default values and optional
    branch/origin/folder from CLI arguments.
    Ensures the directory path exists and handles overwrite logic.
    """
    log(MESSAGES["config_start_creation"].format(name), level='step')
    log(MESSAGES["config_target_output_path"].format(output_filepath), level='normal')

    default_config = {
        "name": name,
        "origin": origin_arg if origin_arg is not None else "origin",
        "branch": branch_arg if branch_arg is not None else "main",
        "git_repo_path": folder_arg if folder_arg is not None else os.path.abspath(os.path.join(os.getcwd(), "path/to/your/local_git_repo")),
        "command_line": "echo 'Your command here (e.g., npm run build, python script.py)'",
        "git_commit_message": f"Automated update for {name}"
    }

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
            json.dump(default_config, f, indent=2)
        log(MESSAGES["config_creation_success"].format(output_filepath), level='success')
        log(MESSAGES["config_edit_hint"], level='normal')
    except Exception as e:
        log(MESSAGES["config_creation_failed"].format(output_filepath, e), level='error')
        sys.exit(1)

    log(MESSAGES["config_finished_creation"].format(name), level='step')