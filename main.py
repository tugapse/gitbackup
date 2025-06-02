# main.py

import argparse
import os
import sys

# Add the project root to the sys.path to ensure modules can be found
script_dir = os.path.dirname(__file__)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from core.workflow_logic import run_task_workflow, run_update_task_workflow
from core.config_operations import (
    create_config_file, edit_config_file, list_tasks,
    get_config_file_path, read_config_file, get_default_config_dir
)
from core.logger import set_verbose, log, clear_log_file
from core.messages import MESSAGES

def main():
    parser = argparse.ArgumentParser(
        description=MESSAGES["cli_description"],
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Positional argument for task_identifier or JSON path
    parser.add_argument(
        'task_identifier',
        nargs='?', # Makes it optional
        help=MESSAGES["cli_task_identifier_help"]
    )

    # Optional arguments
    parser.add_argument(
        '--create',
        action='store_true',
        help=MESSAGES["cli_create_help"]
    )
    parser.add_argument(
        '--json',
        help=MESSAGES["cli_json_help"]
    )
    parser.add_argument(
        '--edit',
        action='store_true',
        help=MESSAGES["cli_edit_help"]
    )
    parser.add_argument(
        '--config-dir',
        default=os.environ.get('GIT_AUTOMATION_CONFIG_DIR', None),
        help=MESSAGES["cli_config_dir_help_env"].format("~/.config/git_automation_configs (Linux/macOS) or %APPDATA%/git_automation_configs (Windows)")
    )
    parser.add_argument(
        '--output',
        help=MESSAGES["cli_output_help"]
    )
    parser.add_argument(
        '--branch',
        help=MESSAGES["cli_branch_override_help"]
    )
    parser.add_argument(
        '--origin',
        help=MESSAGES["cli_origin_override_help"]
    )
    parser.add_argument(
        '--folder', # Changed from --repo-path to --folder for consistency
        help=MESSAGES["cli_folder_help"]
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help=MESSAGES["cli_verbose_help"]
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help=MESSAGES["cli_overwrite_help"]
    )
    parser.add_argument(
        '--initialize',
        action='store_true',
        help=MESSAGES["cli_initialize_help"]
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help=MESSAGES["cli_list_help"]
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help=MESSAGES["cli_update_help"]
    )

    args = parser.parse_args()

    # Set verbose mode in logger FIRST
    set_verbose(args.verbose)
    # Then clear the log file
    clear_log_file()

    # Determine the actual config directory to use
    args.config_dir = get_default_config_dir(args.config_dir)

    # Handle mutually exclusive commands
    command_args = [args.create, args.edit, args.list, args.update]
    if sum(command_args) > 1:
        log(MESSAGES["cli_error_mutually_exclusive_commands"], level='error')
        parser.print_help()
        sys.exit(1)

    if args.list:
        list_tasks(args)
        sys.exit(0)

    if args.create:
        if not args.task_identifier:
            log("❌ Error: --create requires a task identifier (e.g., 'my_task').", level='error')
            parser.print_help()
            sys.exit(1)
        create_config_file(args)
        sys.exit(0)

    if args.edit:
        edit_config_file(args)
        sys.exit(0)

    # Ensure task_identifier or --json is provided for other operations
    if not args.task_identifier and not args.json:
        log(MESSAGES["cli_error_no_task_or_json"], level='error')
        parser.print_help()
        sys.exit(1)

    # Determine the config file path
    config_file_path = args.json if args.json else get_config_file_path(args.task_identifier, args.config_dir)

    # Read the task configuration
    task = read_config_file(config_file_path)

    if task is None:
        sys.exit(1) # Error already logged by read_config_file

    # If --update is specified, run the update workflow
    if args.update:
        # Corrected: Using direct strings for debug messages
        log(f"DEBUG: Inside --update block.", level='debug')
        log(f"DEBUG: args.task_identifier is: {args.task_identifier}", level='debug')
        run_update_task_workflow(args, task, config_file_path) # Call the new update workflow
        log(f"DEBUG: run_update_task_workflow finished. Exiting.", level='debug')
    else:
        # Default behavior: run the regular task workflow
        # Corrected: Using direct strings for debug messages
        log(f"DEBUG: Inside default run block.", level='debug')
        run_task_workflow(args, task, config_file_path)

if __name__ == "__main__":
    main()