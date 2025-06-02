# **Git Automation CLI**

This is a command-line interface (CLI) tool designed to automate common Git tasks, making it easier to manage your repositories, especially for recurring backup or synchronization needs. It allows you to define tasks in simple JSON configuration files and execute them with a single command.

## **Features**

* **Task-Based Automation**: Define specific Git workflows (e.g., pull, commit, push, run custom commands) for different repositories.  
* **Flexible Configuration**: Store task details in JSON files, with options to override settings via command-line arguments.  
* **Streamlined Update Workflow**: A dedicated \--update flag for quick synchronization, automatically skipping pre-commands.  
* **Robust Git Operations**: Includes logic for:  
  * Initializing new repositories.  
  * Adding/updating remote origins.  
  * Checking out/creating branches.  
  * Stashing and popping local changes before pulls to prevent conflicts.  
  * Graceful handling of "no changes to commit" scenarios.  
* **Customizable Commands**: Run arbitrary shell commands before and after Git operations.  
* **Clean & Informative Logging**:  
  * Color-coded console output for easy readability (Success, Step, Info, Warning, Error messages).  
  * Detailed debug logging (visible with \--verbose).  
  * All logs are saved to a dedicated log file for historical tracking.  
* **Graceful Interruption**: Handles Ctrl+C (KeyboardInterrupt) gracefully, exiting without a full traceback.

## **Installation**

1. **Prerequisites**:  
   * **Python 3.x**: Ensure you have Python 3 installed on your system.  
   * **Git**: Ensure Git is installed and accessible in your system's PATH.  
2. **Clone the Repository**:  
   git clone https://github.com/tugapse/gitbackup.git 
   cd gitbackup

3. **No further installation steps are typically required** as this is a standalone Python script.

## **Usage**

The script is run via sh run.sh followed by commands and options.

### **Basic Commands**

* **Run a Task**:  
  sh run.sh \<task\_identifier\>

  Executes the workflow defined in \<config\_dir\>/\<task\_identifier\>.json.  
* **Create a New Task**:  
  sh run.sh \--create \<task\_identifier\> \[options\]

  Creates a new JSON configuration file for a task. You can specify initial folder, branch, and origin.  
* **Edit an Existing Task**:  
  sh run.sh \--edit \<task\_identifier\>

  Opens the task's JSON configuration file in your default system editor (or nano as a fallback).  
* **List All Tasks**:  
  sh run.sh \--list

  Displays a list of all available task configuration files.  
* **Run Update Workflow**:  
  sh run.sh \--update \<task\_identifier\>

  A streamlined workflow that performs a pull, commits any changes, and pushes. It **explicitly skips** any pre\_command or post\_command defined in the task configuration.

### **Key Options**

* \--folder \<path\>: Override the folder (repository path) specified in the task config.  
* \--branch \<name\>: Override the branch specified in the task config.  
* \--origin \<url\>: Override the origin URL specified in the task config.  
* \--verbose: Enable verbose logging, showing detailed debug messages in the console and log file.  
* \--initialize: When running a task, if the specified folder is not a Git repository, this flag will initialize it as one.  
* \--overwrite: When using \--create, this flag allows overwriting an existing task configuration file.  
* \--json \<path/to/config.json\>: Directly specify a JSON configuration file path instead of using a task identifier.

### **Configuration File Structure**

Task configurations are stored as JSON files (e.g., my\_task.json) in your configuration directory (default: \~/.config/git\_automation\_configs/ on Linux/macOS, %APPDATA%/git\_automation\_configs/ on Windows).  
Here's the expected structure of a task JSON file:  
```json
{  
    "name": "my_task_name",                 // (Required) A descriptive name for the task.  
    "folder": "/path/to/your/repository",   // (Required) Absolute path to the Git repository.  
    "branch": "main",                       // (Required) The Git branch to operate on (e.g., "main", "develop").  
    "origin": "https://github.com/user/repo.git", // (Optional) The remote origin URL.  
    "pull_before_command": true,            // (Optional, default: true) Whether to run `git pull` before `pre_command`.  
    "pre_command": "echo 'Running before Git ops'", // (Optional) Shell command to execute before Git add/commit/push.  
    "commit_message": "Automated commit by git-automation", // (Required) The commit message to use.  
    "push_after_command": true,             // (Optional, default: true) Whether to run `git push` after `post_command`.  
    "post_command": "echo 'Running after Git ops'" // (Optional) Shell command to execute after Git add/commit/push.  
}
```
**Note on pre\_command and post\_command**:

* These fields expect a single string that will be executed as a shell command.  
* In \--update mode, pre\_command and post\_command are **always skipped**.

## **Logging**

* **Console Output**: Provides clean, color-coded messages (Success, Step, Info, Warning, Error) without verbose prefixes, allowing for quick visual scanning of the workflow progress and status.  

* **Log File**: A detailed log file (git\_automation.log in your config directory's logs subfolder) captures all messages, including debug output, with timestamps and full context, regardless of the console verbosity setting. This is useful for debugging and auditing past runs.
