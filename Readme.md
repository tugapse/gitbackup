**Git Automation CLI**
=====================

Automate your common Git workflows and manage repository history with ease. This powerful CLI tool streamlines tasks like pulling, committing, pushing, and applying specific changes from remote history, all while providing clear feedback and protecting your work.

Table of Contents
-------------------

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Configuration](#configuration)
5. [Logging](#logging)
6. [Contributing](#contributing)
7. [License](#license)

**Features**
------------

The Git Automation CLI offers a robust set of features to simplify your daily Git operations:

* **Core Workflow Automation:** Automatically pull, add, commit, and push changes to your configured repositories.
* **Intelligent Update Workflow (`--update`):**
  + Handles local uncommitted/unstaged changes gracefully by performing an automatic stash before pulling.
  + Automatically applies the stashed changes back after a successful pull.
  + Ensures clean pulls without manual stash/pop operations.
* **View Remote Commits (`--show-last-commits`):**
  + Quickly displays the last 5 commits from any configured remote branch.
  + Provides essential details like commit hash, message, author, and date.
* **Interactive Cherry-Pick (`--interactive`):**
  + Allows you to selectively apply changes from multiple commits to your local branch.
  + Provides clear instructions for resolving conflicts.
* **Configuration-Driven:** Customizable workflows through JSON configuration files.
* **Detailed Logging:** Comprehensive logging for debugging and auditing.

**Installation**
--------------

To get started with the Git Automation CLI, follow these steps:

1. **Prerequisites:**
  + **Python 3.x:** Ensure you have Python installed.
  + **Git:** Make sure Git is installed and accessible from your terminal.
2. **Clone the Repository:**
  + `git clone https://github.com/tugapse/gitbackup.git`
  + `cd gitbackup`
3. **Set up a Python Virtual Environment (Highly Recommended):**
  + `python3 -m venv venv`
  + On Windows: `.\\venv\\Scripts\\activate.bat` or `source venv/bin/activate`
4. Install Dependencies:
  + Create a `requirements.txt` file in your project root with necessary Python packages (e.g., pyinstaller if you plan to build executables).
  + Then install them: `pip install -r requirements.txt`

**Usage**
--------

The `gitb` command is your entry point, executed via `run.sh` (Linux/macOS) or `run.cmd` (Windows). All operations require a task identifier (the name of your configuration file without the `.json` extension), unless you're listing tasks or specifying a direct JSON file.

### Basic Commands:

* **Run a Task:**
  + Linux/macOS: `sh run.sh <task_identifier>`
  + Example: `sh run.sh my_project_backup`
  + Windows: `run.cmd <task_identifier>`
  + Example: `run.cmd my_project_backup`

This executes the configured pull, pre_command, add, commit, push, and post_command sequence.

* **Create a New Task Configuration:**
  + Linux/macOS: `sh run.sh --create <new_task_name> [--folder /path/to/repo] [--branch main] [--origin https://...}`
  + Example: `sh run.sh --create dev_workflow --folder ~/Code/my-app --branch develop`
  + Windows: `run.cmd --create <new_task_name> [--folder C:\\path\\to\\repo] [--branch main] [--origin https://...]`
  + Example: `run.cmd --create dev_workflow --folder C:\\Users\\YourUser\\Code\\my-app --branch develop`

This creates a new JSON config file with default settings in your configuration directory.

* **Edit an Existing Task Configuration:**
  + Linux/macOS: `sh run.sh --edit <task_identifier>`
  + Example: `sh run.sh --edit my_project_backup`
  + Windows: `run.cmd --edit <task_identifier>`
  + Example: `run.cmd my_project_backup`

This opens the specified task's JSON file in your default editor (EDITOR or VISUAL environment variable, or nano).

* **List All Available Tasks:**
  + Linux/macOS: `sh run.sh --list`
  + Windows: `run.cmd --list`

### New Advanced Workflows:

* **Perform an Intelligent Update (`--update`):**
  + Linux/macOS: `sh run.sh --update <task_identifier>`
  + Example: `sh run.sh --update my_project_backup`
  + Windows: `run.cmd --update <task_identifier>`
  + Example: `run.cmd my_project_backup`

This is similar to the default run but specifically designed to handle local changes by stashing them before pulling and popping them afterward, ensuring a clean pull. It skips pre_command and post_command.

* **Show Last Remote Commits (`--show-last-commits`):**
  + Linux/macOS: `sh run.sh --show-last-commits <task_identifier>`
  + Example: `sh run.sh --show-last-commits my_project_backup`
  + Windows: `run.cmd --show-last-commits <task_identifier>`
  + Example: `run.cmd my_project_backup`

This displays a numbered list of the last 5 commits on the configured remote branch, including commit hash, message, author, and date.

* **Interactively Cherry-Pick a Commit (`--revert-commit`):**
  + Linux/macOS: `sh run.sh --revert-commit <task_identifier>`
  + Example: `sh run.sh --revert-commit my_project_backup`
  + Windows: `run.cmd --revert-commit <task_identifier>`
  + Example: `run.cmd my_project_backup`

This allows you to selectively apply changes from multiple commits to your local branch. It provides clear instructions for resolving conflicts.

### Global Options:

* **`--verbose`:** Enable verbose output, showing detailed Git command executions and internal process logs.
* **`--json <path_to_file.json>`:** Specify a direct path to a JSON configuration file instead of using a task identifier.
* **`--config-dir <path>`:** Override the default configuration directory.
* **`--branch <branch_name>`:** Override the branch specified in the task configuration.
* **`--origin <url>`:** Override the origin URL specified in the task configuration.
* **`--folder <path>`:** Override the repository folder specified in the task configuration.
* **`--overwrite`:** When used with `--create`, overwrites an existing task configuration file.
* **`--initialize`:** Initialize the folder as a Git repository if it's not already one.

**Configuration**
--------------

Task configurations are stored in JSON files. By default, these are located in:

* **Linux/macOS:** `~/.config/git_automation_configs/`
* **Windows:** `%APPDATA%\git_automation_configs\`

Each file is named `<task_identifier>.json`.

### Example `my_project_backup.json`:
```json
{
  "name": "my_project_backup",
  "folder": "/home/user/my_projects/my_app_repo",
  "branch": "main",
  "origin": "https://github.com/myuser/my-app.git",
  "pull_before_command": true,
  "pre_command": "npm install && npm run build",
  "commit_message": "Automated daily backup",
  "push_after_command": true,
  "post_command": "echo \"Backup complete!\"",
  "timestamp_format": "%Y-%m-%d %H:%M:%S"
}
```

### Configuration Fields:

* `"name"` (string): A descriptive name for the task.
* `"folder"` (string): **Required.** The absolute path to the Git repository folder.
* `"branch"` (string): The Git branch to operate on (e.g., `main`, `develop`, `feature/xyz`). Defaults to `"main"`.
* `"origin"` (string): The URL of the remote origin (e.g., `https://github.com/user/repo.git`).
* `"pull_before_command"` (boolean): If `true`, a `git pull origin <branch>` is performed before `pre_command` and commit operations.
* `"pre_command"` (string): An optional shell command to execute before Git `add`/`commit`/`push`.
* `"commit_message"` (string): The base message for the automated Git commit.
* `"push_after_command"` (boolean): If `true`, a `git push origin <branch>` is performed after the commit.
* `"post_command"` (string): An optional shell command to execute after Git `add`/`commit`/`push`.
* `"timestamp_format"` (string): Defines the strftime format for a timestamp appended to `commit_message`. If empty or omitted, no timestamp is added.

**Logging**
---------

All CLI operations are logged to a file for review and debugging:

* **Log File Location:** `~/.config/git_automation_configs/git_automation.log`

**Contributing**
----------------

Contributions are welcome!
