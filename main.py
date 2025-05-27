import os
import json
import sys

# Import our custom argument parser from the 'core' subdirectory
from core.cli_parser import parse_arguments

# Import functions from our logic modules from the 'core' subdirectory
from core.command_logic import execute_command
from core.git_logic import pull_updates, diff_changes, add_commit_changes, push_updates # <-- Added push_updates

def create_config_file(name, output_filepath, branch_arg=None, origin_arg=None, folder_arg=None):
    """
    Creates a new JSON configuration file with default values and optional
    branch/origin/folder from CLI arguments.
    Ensures the directory path exists.
    """
    # Use provided arguments, otherwise default placeholders
    default_config = {
        "name": name,
        "origin": origin_arg if origin_arg is not None else "origin", # Changed default to 'origin' for new configs
        "branch": branch_arg if branch_arg is not None else "main",
        "git_repo_path": folder_arg if folder_arg is not None else os.path.abspath(os.path.join(os.getcwd(), "path/to/your/local_git_repo")), # Placeholder
        "command_line": "echo 'Your command here (e.g., npm run build, python script.py)'",
        "git_commit_message": f"Automated update for {name}"
    }

    # Ensure the output filename has a .json extension
    if not output_filepath.lower().endswith(".json"):
        output_filepath += ".json"

    # Get the directory part of the output_filepath
    output_dir = os.path.dirname(output_filepath)
    # If the path included a directory, ensure it exists
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"Created directory: '{output_dir}'")
        except Exception as e:
            print(f"Error creating directory '{output_dir}': {e}")
            sys.exit(1)

    try:
        with open(output_filepath, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Successfully created configuration file: '{output_filepath}'")
        print("\nPlease edit this file with your specific paths and commands.")
    except Exception as e:
        print(f"Error creating configuration file '{output_filepath}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Parse command-line arguments using our dedicated parser
    args = parse_arguments()

    # --- Handle --create command ---
    if args.create:
        task_name_for_creation = args.create
        if args.output:
            output_filepath = args.output
        else:
            output_filepath = f"{task_name_for_creation.replace(' ', '_').lower()}.json"
            output_filepath = os.path.abspath(output_filepath)

        # Pass all relevant CLI arguments to create_config_file
        create_config_file(
            task_name_for_creation,
            output_filepath,
            branch_arg=args.branch,
            origin_arg=args.origin,
            folder_arg=args.folder
        )
        sys.exit(0)

    # --- Handle running a task from config_file (existing logic) ---
    config_file_path = args.config_file

    if not os.path.exists(config_file_path):
        print(f"Error: Configuration file '{config_file_path}' not found.")
        sys.exit(1)

    try:
        with open(config_file_path, 'r') as f:
            task = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{config_file_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading '{config_file_path}': {e}")
        sys.exit(1)

    if not isinstance(task, dict):
        print(f"Error: JSON file '{config_file_path}' must contain a single JSON object (not a list or other type).")
        sys.exit(1)

    print(f"--- Starting automated task from '{config_file_path}' ---")

    # Extract properties from JSON
    task_name = task.get("name", "Unnamed Task")
    command_line = task.get("command_line")
    git_commit_message = task.get("git_commit_message", f"Automated update for {task_name}")

    # Determine git_repo_path: CLI arg takes precedence, then config
    git_repo_path = args.folder if args.folder is not None else task.get("git_repo_path")

    # Determine branch: CLI arg takes precedence, then config, then default
    branch = args.branch if args.branch is not None else task.get("branch", "main")

    # Determine origin: CLI arg takes precedence, then config, then default
    origin = args.origin if args.origin is not None else task.get("origin", "origin")

    print(f"\nTask Details: {task_name}")
    print(f"  Git Repo Path: '{git_repo_path}' (from {'CLI' if args.folder is not None else 'config'})")
    print(f"  Branch: '{branch}' (from {'CLI' if args.branch is not None else 'config/default'})")
    print(f"  Origin: '{origin}' (from {'CLI' if args.origin is not None else 'config/default'})")
    if command_line:
        print(f"  Pre-commit Command: '{command_line}'")
    else:
        print("  No pre-commit command specified.")
    print(f"  Git Commit Message: '{git_commit_message}'")
    print("-" * 60)

    # --- Pre-requisite checks ---
    if not git_repo_path:
        print(f"  Error for '{task_name}': 'git_repo_path' is missing in config.json and not provided via --folder.")
        print("--- Task aborted due to missing essential information. ---")
        sys.exit(1)

    if not os.path.isdir(git_repo_path) or not os.path.exists(os.path.join(git_repo_path, '.git')):
        print(f"  Error for '{task_name}': Defined Git repository path '{git_repo_path}' is not a valid Git repository or does not exist.")
        print("--- Task aborted as Git repository is not set up correctly. ---")
        sys.exit(1)

    # --- Workflow Steps ---

    # 1. Git Pull (initial)
    print("\n--- Step 1: Performing initial Git Pull ---")
    if not pull_updates(git_repo_path, branch=branch, task_name=task_name):
        print(f"--- Task '{task_name}' aborted: Initial Git Pull failed. ---")
        sys.exit(1)

    # 2. Run Command
    print("\n--- Step 2: Executing command_line ---")
    if command_line:
        if not execute_command(command_line, task_name):
            print(f"--- Task '{task_name}' aborted: Command execution failed. ---")
            sys.exit(1)
    else:
        print("  No command_line to execute.")

    # 3. Check for changed files (git diff)
    print("\n--- Step 3: Checking for changes in Git Repository ---")
    changes_found = diff_changes(git_repo_path, task_name)
    if changes_found is None:
        print(f"--- Task '{task_name}' aborted: Failed to check for Git differences. ---")
        sys.exit(1)

    # 4. Git Add + Commit (if changes found)
    commit_successful = False # Flag to track if commit happened
    if changes_found:
        print("\n--- Step 4: Changes detected. Performing Git Add and Commit ---")
        if add_commit_changes(git_repo_path, git_commit_message, ".", task_name):
            commit_successful = True
        else:
            print(f"--- Task '{task_name}' aborted: Git Add/Commit failed. ---")
            sys.exit(1)
    else:
        print("\n--- Step 4: No changes detected. Skipping Git Add and Commit. ---")

    # 5. Git Push (if a commit just occurred)
    if commit_successful:
        print("\n--- Step 5: Commits made. Performing Git Push ---")
        if not push_updates(git_repo_path, branch=branch, origin=origin, task_name=task_name):
            print(f"--- Task '{task_name}' completed with warnings: Git Push failed. ---")
            sys.exit(1) # Consider if you want to exit on push failure or just warn
    else:
        print("\n--- Step 5: No new commits to push. Skipping Git Push. ---")


    # 6. Final Git Pull (Moved to Step 6)
    # This step ensures the local repo is fully synced after your push,
    # in case other changes landed while your script was running.
    print("\n--- Step 6: Performing final Git Pull (post-push sync) ---")
    if not pull_updates(git_repo_path, branch=branch, task_name=task_name):
        print(f"--- Task '{task_name}' completed with warnings: Final Git Pull failed. ---")
        sys.exit(1) # Or just warn, depending on desired strictness

    print(f"\n--- Task '{task_name}' completed successfully! ---")