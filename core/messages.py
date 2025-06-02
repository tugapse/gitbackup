MESSAGES = {
    # --- CLI Descriptions and Help ---
    "cli_description": "Git Automation CLI: Automates common Git tasks like pulling, committing, and pushing.\n\n"
                     "Usage:\n"
                     "  sh run.sh <task_identifier> [--options...]\n"
                     "  sh run.sh --create <task_identifier> [--options...]\n"
                     "  sh run.sh --edit <task_identifier>\n"
                     "  sh run.sh --list\n"
                     "  sh run.sh --update <task_identifier> [--options...]\n\n"
                     "Examples:\n"
                     "  sh run.sh my_dev_task\n"
                     "  sh run.sh --create new_feature --folder /path/to/repo --branch feature/XYZ\n"
                     "  sh run.sh --edit my_dev_task\n"
                     "  sh run.sh --list\n"
                     "  sh run.sh --update my_dev_task --verbose\n",

    "cli_task_identifier_help": "Identifier for the task configuration. Not needed for --list.",
    "cli_create_help": "Create a new task configuration file. Requires <task_identifier>.",
    "cli_json_help": "Specify a direct path to a JSON configuration file instead of using a task identifier.",
    "cli_edit_help": "Open an existing task configuration file for editing. Requires <task_identifier>.",
    "cli_config_dir_help_env": "Specify a custom directory for task configurations. Overrides XDG_CONFIG_HOME or APPDATA. (Default: {})",
    "cli_output_help": "Redirect output to a file (not yet implemented).",
    "cli_branch_override_help": "Override the branch specified in the task configuration.",
    "cli_origin_override_help": "Override the origin URL specified in the task configuration.",
    "cli_folder_help": "Override the repository folder specified in the task configuration.",
    "cli_verbose_help": "Enable verbose logging, showing debug messages.",
    "cli_overwrite_help": "Overwrite an existing task configuration file when using --create.",
    "cli_initialize_help": "Initialize the folder as a Git repository if it's not already one.",
    "cli_list_help": "List all available task configuration files.",
    "cli_update_help": "Run the task in 'update' mode (skips pre/post commands, focuses on pull/commit/push).",

    # --- CLI Errors ---
    "cli_error_mutually_exclusive_commands": "Only one command (--create, --edit, --list, --update) can be specified.",
    "cli_create_requires_task_identifier": "The --create command requires a <task_identifier>.",
    "cli_error_no_task_or_json": "Please specify a task identifier or a JSON config file path (--json).",

    # --- Config Operations ---
    "config_warning_unknown_os": "Could not determine standard config directory for this OS. Using current working directory for configs.",
    "config_error_no_config_dir": "Configuration directory path is not defined.",
    "config_error_file_exists": "Configuration file already exists at {}. Use --overwrite to force overwrite.",
    "config_use_overwrite_option": "To overwrite, run with the --overwrite flag.",
    "config_created_successfully": "Configuration file created at {}.",
    "config_edit_recommendation": "You can now edit the configuration for '{}' using 'sh run.sh --edit {}' to customize settings.",
    "config_error_creating_file": "Failed to create configuration file {}: {}",
    "config_error_edit_file_not_found": "Configuration file for '{}' not found. Cannot edit.",
    "config_create_recommendation": "Create it first using 'sh run.sh --create {}'.",
    "config_opened_for_editing": "Opened {} for editing.",
    "config_error_editor_not_found": "Could not find editor '{}'. Please set EDITOR or VISUAL environment variables.",
    "config_error_editor_exit": "Editor '{}' exited with an error: {}",
    "config_error_editing_file": "An error occurred while trying to edit file {}: {}",
    "config_no_config_dir_found": "Configuration directory '{}' not found or is not a directory. No tasks to list.",
    "config_listing_tasks": "Listing available tasks in: {}",
    "config_no_tasks_found": "No task configuration files found.",
    "config_error_file_not_found": "Configuration file not found at {}.",
    "config_reading_file": "Reading configuration from: {}",
    "config_error_invalid_json": "Invalid JSON in configuration file {}: {}",
    "config_error_reading_file": "An error occurred while reading configuration file {}: {}",

    # --- Workflow Logic ---
    "workflow_start": "Starting workflow for task '{}'.",
    "workflow_creating_folder": "Creating repository folder: {}",
    "workflow_folder_created": "Folder created.",
    "workflow_folder_creation_failed": "Failed to create folder {}: {}",
    "workflow_executing_pre_command": "Executing pre-command...",
    "workflow_pre_command_failed": "Pre-command failed.",
    "workflow_pre_command_successful": "Pre-command completed.",
    "workflow_executing_post_command": "Executing post-command...",
    "workflow_post_command_failed": "Post-command failed.",
    "workflow_post_command_successful": "Post-command completed.",
    "workflow_completed": "Workflow completed for task '{}'.",
    "workflow_task_failed_loading": "Task configuration could not be loaded or was invalid.",
    
    # --- Update Workflow Specific ---
    "update_workflow_start": "Starting update workflow for task '{}'.",
    "update_workflow_completed": "Update workflow completed for task '{}'.",
    "update_error_folder_not_found": "Repository folder '{}' not found for update. Please run a full task workflow first or manually create it.",
    "update_error_not_git_repo": "Folder '{}' is not a Git repository. Cannot perform update. Run a full task workflow with --initialize.",

    # --- Git Commands ---
    "git_executing_command": "Executing Git command: {}", # This will be DEBUG level, so not printed by default
    "git_command_failed": "Git command '{}' failed with exit code {}.",
    "git_command_exception": "An exception occurred during Git command '{}': {}",
    "git_not_found": "Git command not found. Please ensure Git is installed and in your PATH.",
    "git_initializing_repo": "Initializing Git repository in '{}'.",
    "git_repo_initialized": "Git repository initialized.",
    "git_adding_remote": "Adding remote origin: {}",
    "git_checking_remote": "Checking remote origin status for: {}", # This will be DEBUG level
    "git_checking_out_branch": "Checking out branch '{}'.",
    "git_on_branch": "On branch '{}'.",
    "git_branch_checkout_failed": "Failed to checkout branch '{}'.",
    "git_branch_checkout_failed_try_create": "Failed to checkout branch '{}'. Attempting to create it.",
    "git_branch_creation_failed": "Failed to create and checkout branch '{}'.",
    "git_not_repo_and_not_init": "Folder '{}' is not a Git repository and --initialize was not specified. Cannot proceed.",
    "git_pulling_latest": "Pulling latest changes...",
    "git_pull_successful": "Git pull successful.",
    "git_adding_changes": "Adding all changes to staging...",
    "git_changes_added": "Changes added to staging.",
    "git_committing_changes": "Committing changes...",
    "git_changes_committed": "Changes committed.",
    "git_no_changes_to_commit": "No changes to commit.",
    "git_pushing_changes": "Pushing changes to remote branch '{}'...",
    "git_push_successful": "Git push successful.",

    # --- General Command Execution ---
    "cmd_executing": "Executing command: '{}'",
    "cmd_finished_successfully": "Command finished successfully.",
    "cmd_failed_exit_code": "Command '{}' failed with exit code {}.",
    "cmd_not_found": "Command '{}' not found.",
    "cmd_exception": "An exception occurred during command '{}': {}",
}