import os
import json
import sys
from core.logger import log

def create_config_file(name, output_filepath, branch_arg=None, origin_arg=None, folder_arg=None, overwrite_flag=False):
    """
    Creates a new JSON configuration file with default values and optional
    branch/origin/folder from CLI arguments.
    Ensures the directory path exists and handles overwrite logic.
    """
    log(f"Starting configuration file creation for task: '{name}'", level='step')
    log(f"Target output path: '{output_filepath}'", level='normal')

    default_config = {
        "name": name,
        "origin": origin_arg if origin_arg is not None else "origin",
        "branch": branch_arg if branch_arg is not None else "main",
        "git_repo_path": folder_arg if folder_arg is not None else os.path.abspath(os.path.join(os.getcwd(), "path/to/your/local_git_repo")),
        "command_line": "echo 'Your command here (e.g., npm run build, python script.py)'",
        "git_commit_message": f"Automated update for {name}"
    }

    # Ensure .json extension if not already present
    if not output_filepath.lower().endswith(".json"):
        output_filepath += ".json"
        log(f"Appended '.json' extension to output path: '{output_filepath}'", level='normal')

    # Check for file existence and handle overwrite
    if os.path.exists(output_filepath):
        if not overwrite_flag:
            log(f"Error: Configuration file '{output_filepath}' already exists. Use --overwrite to force creation.", level='error')
            sys.exit(1)
        else:
            log(f"Warning: Configuration file '{output_filepath}' already exists. Overwriting as --overwrite was specified.", level='normal')

    output_dir = os.path.dirname(output_filepath)
    if output_dir and not os.path.exists(output_dir):
        log(f"Parent directory '{output_dir}' does not exist. Attempting to create...", level='normal')
        try:
            os.makedirs(output_dir, exist_ok=True)
            log(f"Successfully created directory: '{output_dir}'", level='normal')
        except Exception as e:
            log(f"Error creating directory '{output_dir}': {e}", level='error')
            sys.exit(1)
    elif not output_dir:
        output_dir = os.getcwd()
        log(f"Output file will be created in the current working directory: '{output_dir}'", level='normal')
    else:
        log(f"Parent directory '{output_dir}' already exists.", level='normal')

    try:
        with open(output_filepath, 'w') as f:
            json.dump(default_config, f, indent=2)
        log(f"Successfully created configuration file: '{output_filepath}'", level='success')
        log("\nPlease edit this file with your specific paths and commands.", level='normal')
    except Exception as e:
        log(f"Error creating configuration file '{output_filepath}': {e}", level='error')
        sys.exit(1)

    log(f"Finished configuration file creation for task: '{name}'", level='step')