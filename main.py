import os
import json
import sys
from datetime import datetime # Import datetime for timestamping config files

# Import our custom argument parser
from core.cli_parser import parse_arguments

# Import functions from our logic modules
from core.command_logic import execute_command
from core.git_logic import pull_updates, diff_changes, add_commit_changes, push_updates

# Import the new logger functions
from core.logger import set_verbose, log

def create_config_file(name, output_filepath, branch_arg=None, origin_arg=None, folder_arg=None):
    """
    Creates a new JSON configuration file with default values and optional
    branch/origin/folder from CLI arguments.
    Ensures the directory path exists.
    """
    log(f"Attempting to create new configuration file for task: '{name}'", level='normal')
    log(f"Target output path: '{output_filepath}'", level='normal')

    default_config = {
        "name": name,
        "origin": origin_arg if origin_arg is not None else "origin",
        "branch": branch_arg if branch_arg is not None else "main",
        "git_repo_path": folder_arg if folder_arg is not None else os.path.abspath(os.path.join(os.getcwd(), "path/to/your/local_git_repo")),
        "command_line": "echo 'Your command here (e.g., npm run build, python script.py)'",
        "git_commit_message": f"Automated update for {name}"
    }

    # Ensure .json extension if not already present (this part is fine)
    if not output_filepath.lower().endswith(".json"):
        output_filepath += ".json"
        log(f"Appended '.json' extension to output path: '{output_filepath}'", level='normal')


    output_dir = os.path.dirname(output_filepath)
    # If the output_filepath includes a directory, ensure it exists
    if output_dir and not os.path.exists(output_dir):
        log(f"Parent directory '{output_dir}' does not exist. Attempting to create...", level='normal')
        try:
            os.makedirs(output_dir, exist_ok=True)
            log(f"Successfully created directory: '{output_dir}'", level='normal')
        except Exception as e:
            log(f"Error creating directory '{output_dir}': {e}", level='error')
            sys.exit(1)
    elif not output_dir: # Case where output_filepath is just a filename in CWD
        output_dir = os.getcwd() # For logging purposes
        log(f"Output file will be created in the current working directory: '{output_dir}'", level='normal')
    else: # Directory already exists
        log(f"Parent directory '{output_dir}' already exists.", level='normal')

    try:
        with open(output_filepath, 'w') as f:
            json.dump(default_config, f, indent=2)
        log(f"Successfully created configuration file: '{output_filepath}'", level='normal')
        log("\nPlease edit this file with your specific paths and commands.", level='normal')
    except Exception as e:
        log(f"Error creating configuration file '{output_filepath}': {e}", level='error')
        sys.exit(1)


if __name__ == "__main__":
    args = parse_arguments()

    # Set verbosity based on CLI argument before any logging occurs
    set_verbose(args.verbose)

    # --- Determine the base directory for configs (either default or user-specified) ---
    # args.config_dir now defaults to ~/git_automation_configs (from cli_parser.py)
    effective_config_base_dir = os.path.abspath(args.config_dir)

    # Create the config base directory if it doesn't exist
    # This ensures ~/git_automation_configs (or custom path) is ready
    if not os.path.exists(effective_config_base_dir):
        try:
            os.makedirs(effective_config_base_dir, exist_ok=True)
            log(f"Created default config directory: '{effective_config_base_dir}'", level='normal')
        except Exception as e:
            log(f"Error creating default config directory '{effective_config_base_dir}': {e}", level='error')
            sys.exit(1)

    # --- Handle --create command ---
    if args.create:
        task_name_for_creation = args.create
        if args.output:
            # User specified a full output path with -o/--output, use it directly
            output_filepath = args.output
        else:
            # THIS IS THE CRUCIAL PART FOR THE BUG FIX:
            # Default output path for creation: effective_config_base_dir + task name + timestamp + .json
            # Replace spaces with underscores for filename compatibility
            base_filename = f"{task_name_for_creation.replace(' ', '_').lower()}"
            current_timestamp = datetime.now().strftime("%m%d%H%M%S") # Generate timestamp here
            output_filepath = os.path.join(effective_config_base_dir, f"{base_filename}_{current_timestamp}.json")

        # The create_config_file function now has improved logging internally
        create_config_file(
            task_name_for_creation,
            output_filepath,
            branch_arg=args.branch,
            origin_arg=args.origin,
            folder_arg=args.folder
        )
        sys.exit(0)

    # --- Determine the configuration file path for running a task ---
    config_file_path = None

    if args.json:
        # If --json is provided, it takes the highest precedence
        config_file_path = args.json
    elif args.task_identifier:
        if args.task_identifier.lower().endswith(".json"):
            # If the positional argument looks like a filename, use it directly
            config_file_path = args.task_identifier
        else:
            # Otherwise, treat it as a task name and construct the path
            # within the effective_config_base_dir
            config_file_path = os.path.join(effective_config_base_dir, f"{args.task_identifier}.json")

    # If no config identifier or --json was provided, then we can't run a task
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
        log("  Create a new config (defaults to user home config dir, with timestamp):", level='normal')
        log("    python main.py --create \"New Workflow\"", level='normal')
        sys.exit(1)

    # From here downwards, the rest of your main.py logic should remain the same
    # as it now correctly uses the determined `config_file_path`
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

    log(f"--- Starting automated task from '{config_file_path}' ---", level='step')

    task_name = task.get("name", "Unnamed Task")
    command_line = task.get("command_line")
    git_commit_message = task.get("git_commit_message", f"Automated update for {task_name}")

    git_repo_path = args.folder if args.folder is not None else task.get("git_repo_path")
    branch = args.branch if args.branch is not None else task.get("branch", "main")
    origin = args.origin if args.origin is not None else task.get("origin", "origin")

    log(f"\nTask Details: {task_name}", level='normal')
    log(f"  Git Repo Path: '{git_repo_path}' (from {'CLI' if args.folder is not None else 'config'})", level='normal')
    log(f"  Branch: '{branch}' (from {'CLI' if args.branch is not None else 'config/default'})", level='normal')
    log(f"  Origin: '{origin}' (from {'CLI' if args.origin is not None else 'config/default'})", level='normal')
    if command_line:
        log(f"  Pre-commit Command: '{command_line}'", level='normal')
    else:
        log("  No pre-commit command specified.", level='normal')
    log(f"  Git Commit Message: '{git_commit_message}'", level='normal')
    log("-" * 60, level='normal')

    # --- Pre-requisite checks ---
    if not git_repo_path:
        log(f"Error for '{task_name}': 'git_repo_path' is missing in config.json and not provided via --folder.", level='error')
        log("--- Task aborted due to missing essential information. ---", level='error')
        sys.exit(1)

    if not os.path.isdir(git_repo_path) or not os.path.exists(os.path.join(git_repo_path, '.git')):
        log(f"Error for '{task_name}': Defined Git repository path '{git_repo_path}' is not a valid Git repository or does not exist.", level='error')
        log("--- Task aborted as Git repository is not set up correctly. ---", level='error')
        sys.exit(1)

    # --- Workflow Steps ---

    log("\n--- Step 1: Performing initial Git Pull ---", level='step')
    if not pull_updates(git_repo_path, branch=branch, task_name=task_name):
        log(f"--- Task '{task_name}' aborted: Initial Git Pull failed. ---", level='error')
        sys.exit(1)

    log("\n--- Step 2: Executing command_line ---", level='step')
    if command_line:
        if not execute_command(command_line, task_name):
            log(f"--- Task '{task_name}' aborted: Command execution failed. ---", level='error')
            sys.exit(1)
    else:
        log("No command_line to execute.", level='normal', task_name=task_name)

    log("\n--- Step 3: Checking for changes in Git Repository ---", level='step')
    changes_found = diff_changes(git_repo_path, task_name)
    if changes_found is None:
        log(f"--- Task '{task_name}' aborted: Failed to check for Git differences. ---", level='error')
        sys.exit(1)

    commit_successful = False
    if changes_found:
        log("\n--- Step 4: Changes detected. Performing Git Add and Commit ---", level='step')
        if add_commit_changes(git_repo_path, git_commit_message, ".", task_name):
            commit_successful = True
        else:
            log(f"--- Task '{task_name}' aborted: Git Add/Commit failed. ---", level='error')
            sys.exit(1)
    else:
        log("\n--- Step 4: No changes detected. Skipping Git Add and Commit. ---", level='step')

    if commit_successful:
        log("\n--- Step 5: Commits made. Performing Git Push ---", level='step')
        if not push_updates(git_repo_path, branch=branch, origin=origin, task_name=task_name):
            log(f"--- Task '{task_name}' completed with warnings: Git Push failed. ---", level='error')
            sys.exit(1)
    else:
        log("\n--- Step 5: No new commits to push. Skipping Git Push. ---", level='step')


    log("\n--- Step 6: Performing final Git Pull (post-push sync) ---", level='step')
    if not pull_updates(git_repo_path, branch=branch, task_name=task_name):
        log(f"--- Task '{task_name}' completed with warnings: Final Git Pull failed. ---", level='error')
        sys.exit(1)

    log(f"\n--- Task '{task_name}' completed successfully! ---", level='step')