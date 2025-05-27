# Git Automation Script

This script provides a simple yet powerful way to automate common Git operations like pulling updates, running pre-commit commands, staging, committing, and pushing changes. It's designed to be highly configurable for different projects and offers precise control over log verbosity.

---

## 🚀 Getting Started

### Prerequisites

Before you dive in, make sure you have:

* **Python 3.x** installed on your system.
* **Git** installed and configured (ensure the `git` command is accessible in your system's PATH).
* A **local Git repository** ready for automation.

### Installation

1.  **Clone this repository** (or simply copy the files) to your local machine:
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git) # Replace with your actual repo URL
    cd your-repo-name
    ```
2.  **Verify your file structure**:
    Your project should be organized like this:
    ```
    your_project/
    ├── main.py
    ├── config.json  # Or your custom config file name
    └── core/
        ├── __init__.py
        ├── cli_parser.py
        ├── command_logic.py
        ├── git_logic.py
        └── logger.py
    ```

---

## 🛠️ Configuration

The script uses straightforward JSON files to define each automated task.

### Creating a New Configuration File

You can generate a new configuration file with default settings right from your terminal:

```bash
python main.py --create "My First Git Task" -o my_task.json
```
    --create "TASK_NAME": This initiates the creation of a new config file, using TASK_NAME as its identifier.
    -o my_task.json: (Optional) Specifies the output filename for your config. If you omit this, the file will be named task_name.json (e.g., my_first_git_task.json).

After creation, a file like my_task.json will appear. You'll need to edit it to fit your project:
JSON

// my_task.json
{
  "name": "My First Git Task",
  "origin": "origin",
  "branch": "main",
  "git_repo_path": "/path/to/your/local_git_repo", // <-- IMPORTANT: Update this path!
  "command_line": "echo 'Your command here (e.g., npm run build, python script.py)'", // <-- Update this command!
  "git_commit_message": "Automated update for My First Git Task"
}

Creating a Configuration File with All Arguments

You can also pre-populate fields like branch, origin, and git_repo_path when creating the file:
Bash

python main.py --create "Dev Branch Workflow" -o dev_workflow.json \
  --branch develop --origin my-fork --folder "/home/user/my_dev_project" --verbose

This command creates dev_workflow.json with develop as the branch, my-fork as the origin, and "/home/user/my_dev_project" as the repository path. It also enables verbose output during the creation process itself.
Editing Your Configuration

Open your generated JSON file (e.g., my_task.json) and carefully modify these key fields:

    name: A clear, descriptive name for your automation task.
    origin: The name of your Git remote (e.g., origin, upstream). Defaults to origin.
    branch: The specific Git branch you want the script to operate on (e.g., main, develop, feature/new-feature). Defaults to main.
    git_repo_path: REQUIRED! The absolute path to your local Git repository. This is vital for the script to locate and manage your code.
    command_line: The shell command to execute before the Git operations. This is perfect for running build processes, tests, data generation, or any other pre-commit actions. Leave it empty ("") if no command is needed.
    git_commit_message: The default commit message to use for automated commits.

🚀 Usage

To run your automated task, simply specify the path to its configuration file:
Bash

python main.py my_task.json

Command-line Overrides

You can temporarily override configuration values for a single run directly from the command line without modifying your JSON file. This is great for flexible execution.

    Override Branch:
    Bash

python main.py my_task.json --branch feature/experimental

Override Origin:
Bash

python main.py my_task.json --origin specific-remote

Override Repository Folder:
Bash

python main.py my_task.json --folder "/another/path/to/your/repo"

Combine Multiple Overrides:
Bash

python main.py my_task.json --branch hotfix/bug-fix --origin fork-origin --folder "/tmp/my_cloned_repo"

Run with Overrides and Verbose Output:
Bash

    python main.py my_task.json --branch production --folder "/var/www/my-app" --verbose

📝 Logging and Verbosity

The script offers two distinct levels of output to suit your needs:

    Default (Concise Output): By default, the script provides a clean overview, showing only the major "Step" messages and critical errors. This is ideal for routine operations where you only need to confirm success or identify high-level failures.
    Bash

python main.py my_task.json

Example Output (Default):

--- Starting automated task from 'my_task.json' ---

--- Step 1: Performing initial Git Pull ---

--- Step 2: Executing command_line ---

--- Step 3: Checking for changes in Git Repository ---

--- Step 4: Changes detected. Performing Git Add and Commit ---

--- Step 5: Commits made. Performing Git Push ---

--- Step 6: Performing final Git Pull (post-push sync) ---

--- Task 'My First Git Task' completed successfully! ---

Verbose Mode: For detailed diagnostics, debugging, or simply to see every operation in action, use the --verbose flag. This will display all internal logs, including Git command outputs (STDOUT/STDERR) and extensive progress messages.
Bash

    python main.py my_task.json --verbose

    Example Output (Verbose - abbreviated):

    --- Starting automated task from 'my_task.json' ---

    Task Details: My First Git Task
      Git Repo Path: '/home/user/Code/my-repo' (from config)
      Branch: 'main' (from config/default)
      Origin: 'origin' (from config/default)
      Pre-commit Command: 'echo "hello"'
      Git Commit Message: 'Automated update for My First Git Task'
    ------------------------------------------------------------

    --- Step 1: Performing initial Git Pull ---
      [My First Git Task] Pulling updates for branch 'main'...
      [My First Git Task] Executing Git command: git pull origin main in '/home/user/Code/my-repo'
      [My First Git Task] Git STDOUT:
    Already up to date.
      [My First Git Task] Git Pull successful.

    --- Step 2: Executing command_line ---
      [My First Git Task] Attempting to execute command: 'echo "hello"'
      [My First Git Task] Command STDOUT:
    hello
      [My First Git Task] Command executed successfully.
    ... (and so on for all steps, including Git STDOUT/STDERR details)

⚙️ Workflow Explained

The script executes a well-defined, sequential workflow for each task:

    Initial Git Pull: Starts by performing a git pull on your specified branch to ensure your local repository is completely up-to-date.
    Execute Pre-commit Command: Runs the shell command defined in your command_line configuration. This is where you'd typically integrate build scripts, tests, or any other necessary pre-commit steps.
    Check for Changes: Scans your Git repository for any modifications, new files, or deletions using git status --porcelain.
    Git Add & Commit: If the script detects any changes in Step 3, it stages all modified and untracked files (git add .) and then creates a new commit using the git_commit_message from your configuration.
    Git Push: If a new commit was successfully created in Step 4, the script pushes your local commits to the remote repository.
    Final Git Pull: Performs one last git pull after the push. This ensures your local repository is fully synchronized with the remote, accounting for any potential concurrent changes or merge resolutions.

🐛 Troubleshooting

    AttributeError: 'Namespace' object has no attribute 'verbose': This error indicates that the --verbose argument hasn't been correctly defined in core/cli_parser.py. Please ensure that file matches the provided code exactly.
    Error: 'git' command not found: This usually means Git isn't installed on your system, or its executable isn't added to your system's PATH.
    Error: ... 'git_repo_path' is missing: Verify that the git_repo_path field is correctly set in your JSON configuration file, or that you've provided it via the --folder command-line argument.
    Error: ... not a valid Git repository: The path you've provided for git_repo_path (or --folder) either doesn't exist or isn't a recognized Git repository.
    Unexpected verbose output: If you're seeing too much detail without the --verbose flag, double-check these:
    Ensure all log() calls in core/git_logic.py and core/command_logic.py use level='normal' for messages you want hidden by default.
    Verify that set_verbose(args.verbose) is called correctly and early in your main.py script.