# core/cli_parser.py

import argparse
import os
from core.messages import MESSAGES

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=MESSAGES["cli_description"],
        formatter_class=argparse.RawTextHelpFormatter # For better multiline help
    )

    # Positional argument for task identifier or JSON path
    parser.add_argument(
        "task_identifier",
        nargs="?", # Makes it optional
        help=MESSAGES["cli_task_identifier_help"]
    )

    # Optional arguments
    parser.add_argument(
        "--create",
        metavar="TASK_NAME",
        help=MESSAGES["cli_create_help"]
    )
    parser.add_argument(
        "--json",
        metavar="PATH_TO_JSON",
        help=MESSAGES["cli_json_help"]
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        help=MESSAGES["cli_edit_help"]
    )
    
    default_config_dir = os.path.join(os.path.expanduser("~"), ".config", "git_automation_configs")
    parser.add_argument(
        "--config-dir",
        default=os.environ.get("GIT_AUTOMATION_CONFIG_DIR", default_config_dir),
        help=MESSAGES["cli_config_dir_help_env"].format(default_config_dir)
    )
    parser.add_argument(
        "--output",
        metavar="FILEPATH",
        help=MESSAGES["cli_output_help"]
    )
    parser.add_argument(
        "--branch",
        metavar="BRANCH_NAME",
        help=MESSAGES["cli_branch_override_help"]
    )
    parser.add_argument(
        "--origin",
        metavar="ORIGIN_URL",
        help=MESSAGES["cli_origin_override_help"]
    )
    parser.add_argument(
        "--folder",
        metavar="REPO_PATH",
        help=MESSAGES["cli_folder_help"]
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=MESSAGES["cli_verbose_help"]
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=MESSAGES["cli_overwrite_help"]
    )
    parser.add_argument(
        "--initialize",
        action="store_true",
        help=MESSAGES["cli_initialize_help"]
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help=MESSAGES["cli_list_help"]
    )
    # ADD THIS NEW ARGUMENT
    parser.add_argument(
        "--update",
        action="store_true",
        help=MESSAGES["cli_update_help"]
    )


    args = parser.parse_args()

    # Special handling for positional argument when other actions are specified
    if args.task_identifier and (args.create or args.edit or args.list or args.update):
        # If a specific action like --create, --edit, --list, or --update is used,
        # and a positional argument is also given, assume positional is the task_identifier
        # for that action, unless --json is also explicitly used.
        pass # The logic below will handle conflicts or use the task_identifier

    # Handle mutual exclusivity for commands that shouldn't be combined
    exclusive_args = [args.create, args.edit, args.list, args.update]
    if sum(1 for x in exclusive_args if x) > 1:
        parser.error(MESSAGES["cli_error_mutually_exclusive_commands"])
        
    return args