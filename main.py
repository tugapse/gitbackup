# main.py

import argparse
import os
import sys

# Add the project root to the sys.path to ensure modules can be found
script_dir = os.path.dirname(__file__)
if script_dir not in sys.path:
    sys.sys.path.insert(0, script_dir)

# Import necessary modules
from core.workflow_logic import (
    run_task_workflow,
    run_update_task_workflow,
    run_show_last_commits_workflow,
    run_revert_commit_workflow,
    run_pull_workflow
)
from core.config_operations import (
    create_config_file, edit_config_file, list_tasks,
    get_config_file_path, read_config_file, get_default_config_dir
)
from core.logger import set_verbose, log, clear_log_file
from core.messages import MESSAGES

def main():
    try: # Start of the KeyboardInterrupt handling try block
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

        # Mutually exclusive group for main commands
        command_group = parser.add_mutually_exclusive_group()
        command_group.add_argument(
            '--create', '-c', # Added -c
            action='store_true',
            help=MESSAGES["cli_create_help"]
        )
        command_group.add_argument(
            '--json', '-j', # Added -j
            help=MESSAGES["cli_json_help"]
        )
        command_group.add_argument(
            '--edit', '-e', # Added -e
            action='store_true',
            help=MESSAGES["cli_edit_help"]
        )
        command_group.add_argument(
            '--list', '-l', # Added -l
            action='store_true',
            help=MESSAGES["cli_list_help"]
        )
        command_group.add_argument(
            '--update', '-u', # Added -u
            action='store_true',
            help=MESSAGES["cli_update_help"]
        )
        command_group.add_argument(
            '--show-last-commits', '-s', # Added -s
            action='store_true',
            help=MESSAGES["cli_show_last_commits_help"]
        )
        command_group.add_argument(
            '--revert-commit', '-r', # Added -r
            action='store_true',
            help=MESSAGES["cli_revert_commit_help"]
        )
        command_group.add_argument(
            '--pull', '-p', # Added -p
            action='store_true',
            help=MESSAGES["cli_pull_help"]
        )

        # Optional arguments (can be combined with task running commands, but not create/edit/list/update)
        parser.add_argument(
            '--config-dir', '-C', # Added -C
            default=os.environ.get('GIT_AUTOMATION_CONFIG_DIR', None),
            help=MESSAGES["cli_config_dir_help_env"].format("~/.config/git_automation_configs (Linux/macOS) or %%APPDATA%%/git_automation_configs (Windows)")
        )
        parser.add_argument(
            '--output', '-o', # Added -o
            help=MESSAGES["cli_output_help"]
        )
        parser.add_argument(
            '--branch', '-b', # Added -b
            help=MESSAGES["cli_branch_override_help"]
        )
        parser.add_argument(
            '--origin', '-O', # Added -O
            help=MESSAGES["cli_origin_override_help"]
        )
        parser.add_argument(
            '--folder', '-f', # Added -f
            help=MESSAGES["cli_folder_help"]
        )
        parser.add_argument(
            '--verbose', '-v', # Added -v
            action='store_true',
            help=MESSAGES["cli_verbose_help"]
        )
        parser.add_argument(
            '--overwrite', '-w', # Added -w
            action='store_true',
            help=MESSAGES["cli_overwrite_help"]
        )
        parser.add_argument(
            '--initialize', '-i', # Added -i
            action='store_true',
            help=MESSAGES["cli_initialize_help"]
        )

        args = parser.parse_args()

        # Set verbose mode in logger FIRST
        set_verbose(args.verbose)
        # Then clear the log file
        clear_log_file()

        # Determine the actual config directory to use
        args.config_dir = get_default_config_dir(args.config_dir)

        if args.list:
            list_tasks(args)
            sys.exit(0)

        if args.create:
            if not args.task_identifier:
                log(MESSAGES["cli_create_requires_task_identifier"], level='error')
                parser.print_help()
                sys.exit(1)
            create_config_file(args)
            sys.exit(0)

        if args.edit:
            if not args.task_identifier:
                log(MESSAGES["cli_edit_requires_task_identifier"], level='error')
                parser.print_help()
                sys.exit(1)
            edit_config_file(args)
            sys.exit(0)

        if args.show_last_commits:
            if not args.task_identifier:
                log(MESSAGES["cli_show_last_commits_requires_task_identifier"], level='error')
                parser.print_help()
                sys.exit(1)
            config_file_path = args.json if args.json else get_config_file_path(args.task_identifier, args.config_dir)
            task = read_config_file(config_file_path)
            if task is None: sys.exit(1)
            run_show_last_commits_workflow(args, task)
            sys.exit(0)

        if args.revert_commit:
            if not args.task_identifier:
                log(MESSAGES["cli_revert_commit_requires_task_identifier"], level='error')
                parser.print_help()
                sys.exit(1)
            config_file_path = args.json if args.json else get_config_file_path(args.task_identifier, args.config_dir)
            task = read_config_file(config_file_path)
            if task is None: sys.exit(1)
            run_revert_commit_workflow(args, task)
            sys.exit(0)
        
        if args.pull:
            if not args.task_identifier:
                log(MESSAGES["cli_pull_requires_task_identifier"], level='error')
                parser.print_help()
                sys.exit(1)
            config_file_path = args.json if args.json else get_config_file_path(args.task_identifier, args.config_dir)
            task = read_config_file(config_file_path)
            if task is None: sys.exit(1)
            run_pull_workflow(args, task)
            sys.exit(0)

        # Ensure task_identifier or --json is provided for other operations (default run or update)
        if not args.task_identifier and not args.json:
            log(MESSAGES["cli_error_no_task_or_json"], level='error')
            parser.print_help()
            sys.exit(1)

        # Determine the config file path for default run or update
        config_file_path = args.json if args.json else get_config_file_path(args.task_identifier, args.config_dir)

        # Read the task configuration
        task = read_config_file(config_file_path)

        if task is None:
            sys.exit(1) # Error already logged by read_config_file

        # If --update is specified, run the update workflow
        if args.update:
            log(f"Inside --update block.", level='debug')
            run_update_task_workflow(args, task, config_file_path)
            log(f"run_update_task_workflow finished. Exiting.", level='debug')
        else:
            # Default behavior: run the regular task workflow
            log(f"Inside default run block.", level='debug')
            run_task_workflow(args, task, config_file_path)

    except KeyboardInterrupt:
        log("\nScript interrupted by user (Ctrl+C). Exiting gracefully.", level='warning')
        sys.exit(1) # Exit with a non-zero code to indicate an interrupted execution
    except Exception as e: # Catch any other unexpected errors
        log(f"An unexpected error occurred: {e}", level='error')
        sys.exit(1)

if __name__ == "__main__":
    main()