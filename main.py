import os
import json
import sys
import subprocess

# Import our custom argument parser
from core.cli_parser import parse_arguments

# Import functions for specific actions
from core.logger import set_verbose, log
from core.workflow_logic import run_task_workflow # Now from core/workflow_logic.py
from core.config_operations import create_config_file # NEW: Imported from core/config_operations.py


if __name__ == "__main__":
    args = parse_arguments()

    set_verbose(args.verbose)

    # Determine the base directory for configs (either default or user-specified)
    effective_config_base_dir = os.path.abspath(args.config_dir)

    # Ensure the config base directory exists at the very beginning
    if not os.path.exists(effective_config_base_dir):
        try:
            os.makedirs(effective_config_base_dir, exist_ok=True)
            log(f"Created default config directory: '{effective_config_base_dir}'", level='normal')
        except Exception as e:
            log(f"Error creating default config directory '{effective_config_base_dir}': {e}", level='error')
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

        # Call the imported create_config_file function
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
            log("Error: No task identifier or --json path provided for editing.", level='error')
            log("Usage: python main.py my_task --edit OR python main.py --json /path/to/my_config.json --edit", level='normal')
            sys.exit(1)

        if not os.path.exists(config_file_path):
            log(f"Error: Configuration file '{config_file_path}' not found for editing.", level='error')
            sys.exit(1)

        log(f"Attempting to open '{config_file_path}' in default editor...", level='step')
        try:
            if sys.platform == "win32":
                os.startfile(config_file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", config_file_path], check=True)
            else:
                subprocess.run(["xdg-open", config_file_path], check=True)
            log(f"Successfully launched editor for '{config_file_path}'.", level='success')
        except FileNotFoundError as e:
            log(f"Error: Default editor command not found. Ensure '{e.filename}' is in your PATH.", level='error')
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            log(f"Error opening file with default editor: {e}", level='error')
            sys.exit(1)
        except Exception as e:
            log(f"An unexpected error occurred while trying to open the file: {e}", level='error')
            sys.exit(1)
        
        sys.exit(0)

    # --- Handle --list command ---
    if args.list:
        log(f"Listing all configured tasks in '{effective_config_base_dir}':", level='step')
        tasks_found = False
        # Redundant os.path.exists check removed here, handled at startup
        if not os.listdir(effective_config_base_dir): # Check if directory is empty
            log(f"No configuration files found in '{effective_config_base_dir}'.", level='info')
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
                        log(f"  Warning: Skipping malformed JSON file: {filename}", level='warning')
                    except KeyError as e:
                        log(f"  Warning: Skipping '{filename}'. Missing expected key: {e}", level='warning')
                    except Exception as e:
                        log(f"  Warning: An unexpected error occurred reading '{filename}': {e}", level='warning')
            
            if not tasks_found:
                log(f"No valid configuration files found in '{effective_config_base_dir}'.", level='info')

        sys.exit(0)

    # --- If none of the above specific actions (create, edit, list) were requested, then proceed to run a task ---
    if not config_file_path:
        log("Error: No task identifier or --json path provided to run a task.", level='error')
        log("Usage Examples:", level='normal')
        log("  Run by task name (e.g., 'my_daily_backup' in default config dir):", level='normal')
        log("    python main.py my_daily_backup", level='normal')
        log("  Run by task name in a specific config directory:", level='normal')
        log("    python main.py my_daily_backup --config-dir ./custom_configs/", level='normal')
        log("  Run by explicit JSON file path:", level='normal')
        log("    python main.py --json /path/to/my_config.json", level='normal')
        log("  Run by explicit JSON file path (positional):", level='normal')
        log("    python main.py ./local_task.json", level='normal')
        log("  Create a new config (defaults to user home config dir):", level='normal')
        log("    python main.py --create \"New Workflow\"", level='normal')
        log("  Create a new config and overwrite if exists:", level='normal')
        log("    python main.py --create \"MyExistingConfig\" --overwrite", level='normal')
        log("  Initialize a new Git repo and run a task:", level='normal')
        log("    python main.py my_new_repo_task --folder /tmp/my_new_repo --initialize --branch dev --origin https://github.com/user/new-repo.git", level='normal')
        log("  Edit an existing config file:", level='normal')
        log("    python main.py my_daily_backup --edit", level='normal')
        log("  List all configured tasks:", level='normal')
        log("    python main.py --list", level='normal')
        sys.exit(1)

    # If we reach here, it means a task needs to be run.
    # Load the task configuration and run the workflow.
    if not os.path.exists(config_file_path):
        log(f"Error: Configuration file '{config_file_path}' not found.", level='error')
        sys.exit(1)

    try:
        with open(config_file_path, 'r') as f:
            task = json.load(f)
    except json.JSONDecodeError as e:
        log(f"Error: Invalid JSON format in '{config_file_path}': {e}", level='error')
        sys.exit(1)
    except Exception as e:
        log(f"An unexpected error occurred while reading '{config_file_path}': {e}", level='error')
        sys.exit(1)

    if not isinstance(task, dict):
        log(f"Error: JSON file '{config_file_path}' must contain a single JSON object (not a list or other type).", level='error')
        sys.exit(1)

    # Call the extracted workflow function
    run_task_workflow(args, task, config_file_path)