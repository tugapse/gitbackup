# core/messages.py

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
    "cli_show_last_commits_help": "Display the last 5 commits from the remote branch.",
    "cli_revert_commit_help": "Interactively select a remote commit to apply as a new change (cherry-pick).",
    "cli_pull_help": "Perform a pull-only operation (fetches and merges, skips commit/push/pre/post commands).", # NEW
    
    # --- CLI Errors (no prefixes) ---
    "cli_error_mutually_exclusive_commands": "Only one command (--create, --edit, --list, --update, --show-last-commits, --revert-commit, --pull) can be specified.", # UPDATED
    "cli_create_requires_task_identifier": "The --create command requires a <task_identifier>.",
    "cli_edit_requires_task_identifier": "The --edit command requires a <task_identifier>.",
    "cli_show_last_commits_requires_task_identifier": "The --show-last-commits command requires a <task_identifier>.",
    "cli_revert_commit_requires_task_identifier": "The --revert-commit command requires a <task_identifier>.",
    "cli_pull_requires_task_identifier": "The --pull command requires a <task_identifier>.", # NEW
    "cli_error_no_task_or_json": "Please specify a task identifier or a JSON config file path (--json).",

    # --- Config Operations (no prefixes) ---
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

    # --- Workflow Logic (no prefixes) ---
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
    "workflow_local_changes_found_stashing": "Local changes detected. Stashing them temporarily...",
    "workflow_stash_failed_before_pull": "Failed to stash local changes before pull.",
    "workflow_no_local_changes_to_stash": "No local changes detected to stash.",
    "workflow_pull_failed_attempting_pop": "Git pull failed, attempting to pop stashed changes...",
    "workflow_pop_stash_failed_after_pull_warning": "Failed to pop stashed changes. There might be conflicts.",
    "workflow_manual_resolve_needed": "Manual intervention required to resolve conflicts or unstage changes.",
    "workflow_pull_before_command_skipped": "Skipping Git pull before command (pull_before_command is false).",
    
    # --- Update Workflow Specific (no prefixes) ---
    "update_workflow_start": "Starting update workflow for task '{}'.",
    "update_workflow_completed": "Update workflow completed for task '{}'.",
    "update_error_folder_not_found": "Repository folder '{}' not found for update. Please run a full task workflow first or manually create it.",
    "update_error_not_git_repo": "Folder '{}' is not a Git repository. Cannot perform update. Run a full task workflow with --initialize.",
    "update_skipping_pre_post_commands": "Skipping pre and post commands in update workflow.",

    # --- Git Commands (no prefixes) ---
    "git_executing_command": "Executing Git command: {}",
    "git_command_failed": "Git command '{}' failed with exit code {}.",
    "git_command_exception": "An exception occurred during Git command '{}': {}",
    "git_not_found": "Git command not found. Please ensure Git is installed and in your PATH.",
    "git_initializing_repo": "Initializing Git repository in '{}'.",
    "git_repo_initialized": "Git repository initialized.",
    "git_adding_remote": "Adding remote origin: {}",
    "git_checking_remote": "Checking remote origin status for: {}",
    "git_checking_out_branch": "Checking out branch '{}'.",
    "git_on_branch": "On branch '{}'.",
    "git_branch_checkout_failed": "Failed to checkout branch '{}'.",
    "git_branch_checkout_failed_try_create": "Failed to checkout branch '{}'. Attempting to create it.",
    "git_branch_creation_failed": "Failed to create and checkout branch '{}'.",
    "git_branch_not_found_local_or_remote": "Branch '{}' not found locally or on remote. Creating new branch.",
    "git_pushing_new_branch": "Pushing new branch '{}' to '{}' as '{}' to set upstream...",
    "git_push_new_branch_failed_warning": "Failed to push new branch '{}' to '{}' as '{}'. You may need to set upstream manually.",
    "git_branch_found_remote": "Branch '{}' found on remote '{}'.",
    "git_branch_found_local": "Branch '{}' found locally.",
    "git_branch_not_found_local": "Branch '{}' not found locally.",
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
    "git_checking_status": "Checking Git status for changes...",
    "git_changes_detected_status_check": "Local changes detected.",
    "git_no_changes_detected_status_check": "No local changes detected.",
    "git_stash_failed": "Git stash failed: {}",
    "git_stash_successful": "Local changes stashed successfully.",
    "git_stash_pop_applying": "Applying stashed changes...",
    "git_stash_pop_no_stash": "No stash entries found to pop.",
    "git_stash_pop_failed_conflict": "Failed to pop stash due to merge conflict. Manual resolution needed.",
    "git_stash_pop_failed_general": "Failed to pop stash: {}",
    "git_stash_pop_successful": "Stashed changes applied successfully.",
    "git_error_status_check": "Failed to check Git status.",
    "git_pull_failed": "Git pull failed for branch '{}'.",
    "git_not_repo_or_not_found": "Repository folder '{}' not found or is not a Git repository.",
    "git_fetch_failed": "Failed to fetch from remote branch '{}'.",
    "git_log_failed": "Failed to retrieve commit log for '{}'.",
    "git_fetching_remote_commits": "Fetching last commits from remote branch '{}'...", 

    # --- Show Last Commits Workflow (no prefixes) ---
    "show_last_commits_start": "Showing last 5 commits for task '{}' on branch '{}'.",
    "show_last_commits_no_commits": "No commits found on remote branch '{}'.",
    "show_last_commits_listing": "Listing last commits on remote branch '{}':",
    "show_last_commits_completed": "Last commits display completed.",

    # --- Revert Commit (Cherry-Pick) Workflow (no prefixes) ---
    "revert_commit_start": "Starting interactive cherry-pick for task '{}'.",
    "revert_error_branch_not_local": "Local branch '{}' not found. Please ensure it exists before attempting to cherry-pick.",
    "revert_auto_stashing_changes": "Local changes detected. Automatically stashing them with message: '{}'.",
    "revert_auto_stash_failed": "Failed to automatically stash local changes. Please resolve manually and try again.",
    "revert_no_local_changes_to_stash": "No local changes detected. Proceeding with cherry-pick.",
    "revert_attempting_pop_after_no_commits": "No commits found to cherry-pick. Attempting to pop stashed changes (if any)...",
    "revert_attempting_pop_after_cancel": "Cherry-pick cancelled. Attempting to pop stashed changes (if any)...",
    "revert_attempting_pop_after_failure": "Cherry-pick or push failed. Attempting to pop stashed changes (if any)...",
    "revert_no_commits_found": "No commits found on remote branch '{}' to cherry-pick from.",
    "revert_listing_commits": "Last 5 commits on remote branch '{}':",
    "revert_prompt_selection": "Enter the number of the commit you want to apply as a new change (1-{}) or 0 to cancel: ",
    "revert_invalid_selection": "Invalid selection. Please enter a number from the list or 0 to cancel.",
    "revert_invalid_input": "Invalid input. Please enter a number.",
    "revert_cancelled": "Cherry-pick operation cancelled.",
    "revert_confirm_cherry_pick": "You are about to apply changes from commit [{}] - '{}' as a NEW commit.",
    "revert_confirm_proceed": "Confirm this action?",
    "revert_performing_cherry_pick": "Performing cherry-pick of commit [{}]...",
    "revert_cherry_pick_failed": "Cherry-pick of commit [{}] failed.",
    "revert_cherry_pick_conflict_instructions": "Merge conflicts detected! Please resolve them manually:\n  1. Use 'git status' to identify conflicted files.\n  2. Edit files to resolve conflicts.\n  3. Use 'git add <resolved_files>' to stage changes.\n  4. Run 'git cherry-pick --continue' to finish.\n  (To abort: 'git cherry-pick --abort')",
    "revert_cherry_pick_successful": "Changes from commit [{}] successfully applied as a new commit.",
    "revert_push_skipped_after_cherry_pick": "Push skipped after cherry-pick (push_after_command is false).",
    "revert_completed": "Interactive cherry-pick workflow completed for task '{}'.",

    # --- New Pull Workflow (no prefixes) ---
    "pull_workflow_start": "Starting pull-only workflow for task '{}'.", # NEW
    "pull_workflow_completed": "Pull-only workflow completed for task '{}'.", # NEW

    # --- General Command Execution (no prefixes) ---
    "cmd_executing": "Executing command: '{}'",
    "cmd_finished_successfully": "Command finished successfully.",
    "cmd_failed_exit_code": "Command '{}' failed with exit code {}.",
    "cmd_not_found": "Command '{}' not found.",
    "cmd_exception": "An exception occurred during command '{}': {}",
}