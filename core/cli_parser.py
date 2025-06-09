import argparse
import os
from core.messages import MESSAGES

def parse_arguments():
    """
    Sets up and parses command-line arguments for the application.
    Returns the parsed arguments object.
    """
    parser = argparse.ArgumentParser(
        description=MESSAGES["cli_description"]
    )

    # --- Mutually exclusive group for core actions: run task, create config, or list configs ---
    group = parser.add_mutually_exclusive_group()

    # Positional argument: can be a task name or a direct config file path (for running OR editing)
    group.add_argument(
        "task_identifier",
        nargs='?', # Makes it optional, as --create, --json, or --list can be used instead
        help=MESSAGES["cli_task_identifier_help"]
    )
    
    # --create flag: for creating a new config file (exclusive with task_identifier)
    group.add_argument(
        "--create",
        metavar="TASK_NAME",
        help=MESSAGES["cli_create_help"]
    )

    # --list flag (added to the mutually exclusive group)
    group.add_argument(
        "--list",
        action="store_true",
        help=MESSAGES["cli_list_help"]
    )

    # --fix-json flag (added to the mutually exclusive group)
    group.add_argument(
        "--fix-json",
        action="store_true",
        help=MESSAGES["cli_fix_json_help"]
    )

    # --- NEW: --update flag (added to the mutually exclusive group) ---
    group.add_argument(
        "--update",
        action="store_true",
        help=MESSAGES["cli_update_help"]
    )
    # --- End new ---


    # --- General options (can be combined with task_identifier or --json, but not --create or --list directly) ---

    # --json flag: explicitly load from a file path (highest precedence for task/edit)
    parser.add_argument(
        "--json",
        metavar="FILEPATH",
        help=MESSAGES["cli_json_help"]
    )

    # --edit flag (moved out of the mutually exclusive group)
    parser.add_argument(
        "--edit",
        action="store_true",
        help=MESSAGES["cli_edit_help"]
    )

    # --config-dir: base directory for task name lookups
    default_config_dir = os.path.join(os.path.expanduser('~'), 'git_automation_configs')
    parser.add_argument(
        "--config-dir",
        metavar="PATH",
        default=default_config_dir,
        help=MESSAGES["cli_config_dir_help"].format(default_config_dir)
    )

    # -o / --output for creation output file
    parser.add_argument(
        "-o", "--output",
        metavar="FILEPATH",
        help=MESSAGES["cli_output_help"]
    )
    
    # Git override arguments (branch, origin, folder)
    parser.add_argument(
        "--branch",
        help=MESSAGES["cli_branch_override_help"]
    )
    parser.add_argument(
        "--origin",
        help=MESSAGES["cli_origin_override_help"]
    )
    parser.add_argument(
        "--folder",
        metavar="GIT_REPO_PATH",
        help=MESSAGES["cli_folder_help"]
    )
    
    # Verbose flag
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=MESSAGES["cli_verbose_help"]
    )

    # Overwrite flag for creation
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=MESSAGES["cli_overwrite_help"]
    )

    # --initialize flag
    parser.add_argument(
        "--initialize",
        action="store_true",
        help=MESSAGES["cli_initialize_help"]
    )

    return parser.parse_args()