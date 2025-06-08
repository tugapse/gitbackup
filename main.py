import os
import json
import sys
import subprocess

# Import our custom argument parser
from core.cli_parser import parse_arguments

# Import functions for specific actions
from core.logger import set_verbose, log
from core.messages import MESSAGES
from core.workflow_logic import run_task_workflow
from core.config_operations import create_config_file, fix_config_files # NEW: Import fix_config_files


if __name__ == "__main__":
    args = parse_arguments()

    set_verbose(args.verbose)

    # Determine the base directory for configs (either default or user-specified)
    effective_config_base_dir = os.path.abspath(args.config_dir)

    # Ensure the config base directory exists at the very beginning
    if not os.path.exists(effective_config_base_dir):
        try:
            os.makedirs(effective_config_base_dir, exist_ok=True)
            log(MESSAGES["config_default_config_path_created"].format(effective_config_base_dir), level='normal')
        except Exception as e:
            log(MESSAGES["config_error_creating_default_config_path"].format(effective_config_base_dir, e), level='error')
            sys.exit(1)

    # --- Determine the configuration file path for running/editing a task ---
    config_file_path = None

    if args.json:
        config_file_path = args.json
    elif args.task_identifier:
        if args.task_identifier.lower().endswith(".json"):
            config_file_path = args.task_identifier
        else:
            config_file_path = os.path.join(effective_config_base_dir, f"{args.task_identifier}.json")
    
    # --- Handle --create command ---
    if args.create:
        task_name_for_creation = args.create
        if args.output:
            output_filepath = args.output
        else:
            base_filename = f"{task_name_for_creation.replace(' ', '_').lower()}"
            output_filepath = os.path.join(effective_config_base_dir, f"{base_filename}.json")

        create_config_file(
            task_name_for_creation,
            output_filepath,
            branch_arg=args.branch,
            origin_arg=args.origin,
            folder_arg=args.folder,
            overwrite_flag=args.overwrite
        )
        sys.exit(0)
    
    # --- Handle --edit command ---
    if args.edit:
        if not config_file_path:
            log(MESSAGES["cli_error_edit_no_args"], level='error')
            log(MESSAGES["cli_edit_usage_hint"], level='normal')
            sys.exit(1)

        if not os.path.exists(config_file_path):
            log(MESSAGES["cli_error_config_file_not_found"].format(config_file_path), level='error')
            sys.exit(1)

        log(MESSAGES["cli_attempting_open_editor"].format(config_file_path), level='step')
        try:
            if sys.platform == "win32":
                os.startfile(config_file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", config_file_path], check=True)
            else:
                subprocess.run(["xdg-open", config_file_path], check=True)
            log(MESSAGES["cli_editor_launched_success"].format(config_file_path), level='success')
        except FileNotFoundError as e:
            log(MESSAGES["cli_error_editor_not_found"].format(e.filename), level='error')
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            log(MESSAGES["cli_error_opening_file_editor"].format(e), level='error')
            sys.exit(1)
        except Exception as e:
            log(MESSAGES["cli_error_unexpected_opening_file"].format(e), level='error')
            sys.exit(1)
        
        sys.exit(0)

    # --- Handle --list command ---
    if args.list:
        log(MESSAGES["cli_listing_tasks_in"].format(effective_config_base_dir), level='step')
        tasks_found = False
        if not os.listdir(effective_config_base_dir):
            log(MESSAGES["cli_no_config_files_found"].format(effective_config_base_dir), level='info')
        else:
            for filename in os.listdir(effective_config_base_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(effective_config_base_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            task = json.load(f)
                            
                        task_name = task.get("name", os.path.splitext(filename)[0])
                        branch = task.get("branch", "N/A")
                        repo_path = task.get("git_repo_path", "N/A")
                        
                        log(f"- {task_name} - {branch}", level='info')
                        log(f"  {repo_path}", level='info')
                        tasks_found = True

                    except json.JSONDecodeError:
                        log(MESSAGES["cli_warning_malformed_json"].format(filename), level='warning')
                    except KeyError as e:
                        log(MESSAGES["cli_warning_missing_key"].format(filename, e), level='warning')
                    except Exception as e:
                        log(MESSAGES["cli_warning_unexpected_error_reading_file"].format(filename, e), level='warning')
            
            if not tasks_found:
                log(MESSAGES["cli_no_valid_configs_found"].format(effective_config_base_dir), level='info')

        sys.exit(0)

    # --- Handle --fix-json command ---
    if args.fix_json:
        fix_config_files(effective_config_base_dir)
        sys.exit(0)

    # --- If none of the above specific actions (create, edit, list, fix-json) were requested, then proceed to run a task ---
    if not config_file_path:
        log(MESSAGES["cli_error_no_task_or_json"], level='error')
        log(MESSAGES["cli_usage_examples"], level='normal')
        log(f"  {MESSAGES['cli_example_run_by_name']}\n    python main.py my_daily_backup", level='normal')
        log(f"  {MESSAGES['cli_example_run_by_name_config_dir']}\n    python main.py my_daily_backup --config-dir ./custom_configs/", level='normal')
        log(f"  {MESSAGES['cli_example_run_by_json_path']}\n    python main.py --json /path/to/my_config.json", level='normal')
        log(f"  {MESSAGES['cli_example_run_by_json_path_positional']}\n    python main.py ./local_task.json", level='normal')
        log(f"  {MESSAGES['cli_example_create_new_config']}\n    python main.py --create \"New Workflow\"", level='normal')
        log(f"  {MESSAGES['cli_example_create_overwrite']}\n    python main.py --create \"MyExistingConfig\" --overwrite", level='normal')
        log(f"  {MESSAGES['cli_example_initialize_run']}\n    python main.py my_new_repo_task --folder /tmp/my_new_repo --initialize --branch dev --origin https://github.com/user/new-repo.git", level='normal')
        log(f"  {MESSAGES['cli_example_edit_config']}\n    python main.py my_daily_backup --edit", level='normal')
        log(f"  {MESSAGES['cli_example_list_tasks']}\n    python main.py --list", level='normal')
        sys.exit(1)

    # If we reach here, it means a task needs to be run.
    # Load the task configuration and run the workflow.
    if not os.path.exists(config_file_path):
        log(MESSAGES["cli_error_config_file_not_found"].format(config_file_path), level='error')
        sys.exit(1)

    try:
        with open(config_file_path, 'r') as f:
            task = json.load(f)
    except json.JSONDecodeError as e:
        log(MESSAGES["cli_error_invalid_json_format"].format(config_file_path, e), level='error')
        sys.exit(1)
    except Exception as e:
        log(MESSAGES["cli_error_unexpected_reading_config"].format(config_file_path, e), level='error')
        sys.exit(1)

    if not isinstance(task, dict):
        log(MESSAGES["cli_error_json_not_object"].format(config_file_path), level='error')
        sys.exit(1)

    # Call the extracted workflow function
    run_task_workflow(args, task, config_file_path)

