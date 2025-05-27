import argparse
import os

def parse_arguments():
    """
    Sets up and parses command-line arguments for the application.
    Returns the parsed arguments object.
    """
    parser = argparse.ArgumentParser(
        description="Automate Git-centric workflows or create new config files."
    )

    # --- Mutually exclusive group for action: run task or create config ---
    group = parser.add_mutually_exclusive_group()

    # Positional argument: can be a task name or a direct config file path
    group.add_argument(
        "task_identifier",
        nargs='?', # Makes it optional, as --create or --json can be used instead
        help="The name of the task (e.g., 'my_backup') which resolves to 'config_dir/my_backup.json', OR a direct path to a config file (e.g., 'path/to/my_config.json')."
    )
    
    # --create flag: for creating a new config file
    group.add_argument(
        "--create",
        metavar="TASK_NAME",
        help="Create a new JSON configuration file with the given task name."
    )

    # --- General options (not mutually exclusive with above) ---

    # --json flag: explicitly load from a file path (highest precedence)
    parser.add_argument(
        "--json",
        metavar="FILEPATH",
        help="Explicitly specify the full path to the JSON configuration file to load. This overrides the positional 'task_identifier' if it was a task name."
    )

    # --config-dir: base directory for task name lookups
    # NEW DEFAULT PATH: User's home directory + 'git_automation_configs' folder
    default_config_dir = os.path.join(os.path.expanduser('~'), 'git_automation_configs')
    parser.add_argument(
        "--config-dir",
        metavar="PATH",
        default=default_config_dir, # Changed default
        help=f"Base directory for looking up config files when only a task name is provided (e.g., 'my_task' resolves to 'PATH/my_task.json'). Defaults to '{default_config_dir}'."
    )

    # -o / --output for creation output file
    parser.add_argument(
        "-o", "--output",
        metavar="FILEPATH",
        help="Specify the output filepath for the new configuration file (used with --create). Defaults to TASK_NAME.json in the current directory."
    )
    
    # Git override arguments (branch, origin, folder)
    parser.add_argument(
        "--branch",
        help="Overrides the 'branch' specified in the config file for this run or pre-fills it during creation."
    )
    parser.add_argument(
        "--origin",
        help="Overrides the 'origin' specified in the config file for this run or pre-fills it during creation."
    )
    parser.add_argument(
        "--folder",
        metavar="GIT_REPO_PATH",
        help="Overrides the 'git_repo_path' specified in the config file for this run or pre-fills it during creation. This should be the absolute path to your local Git repository."
    )
    
    # Verbose flag
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output for detailed logging of operations."
    )

    return parser.parse_args()