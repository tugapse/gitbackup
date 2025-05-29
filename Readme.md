# **Git Automation Script**

This script provides a simple yet powerful way to automate common Git operations like pulling updates, running pre-commit commands, staging, committing, and pushing changes. It's designed to be highly configurable for different projects and offers precise control over its execution and logging.

## **🚀 Getting Started**

### **Prerequisites**

Before you dive in, make sure you have

* **Python 3.x** installed on your system.
* **Git** installed and configured (ensure the git command is accessible in your system's PATH).
* A **local Git repository** (or a path where one can be initialized) ready for automation.

### **Installation**

1. **Clone this repository** (or simply copy the files) to your local machine:
   ```bash
   git clone https://github.com/tugapse/gitbackup.git 
   cd gitbackup
   ```
   Verify your file structure:
   ```
   your_project/
   ├── main.py
   ├── config.json  # Example config, or custom names
   └── core/
       ├── __init__.py
       ├── cli_parser.py
       ├── command_logic.py
       ├── git_logic.py
       ├── logger.py
       ├── config_operations.py # For config creation/management
       └── workflow_logic.py    # For the main workflow
   ```

2. **Set up a Python Virtual Environment** (highly recommended):
   ```bash
   python3 -m venv venv
   # On Windows: .\\venv\\Scripts\\activate.bat
   # On Linux/macOS: source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install pyinstaller # PyInstaller is needed if you plan to build executables
   ```

## **🛠️ Configuration**

The script uses straightforward JSON files to define each automated task. By default, these configuration files are stored in a dedicated folder within your user's home directory: `~/git_automation_configs/`.

### **Creating a New Configuration File (--create)**

You can generate a new configuration file with default settings directly from your terminal.
```bash
python main.py --create "My First Git Task"
```
Or:
```bash
python main.py --create "My Custom Task" -o my_custom_task.json
```

* `--create "TASK_NAME"`: Initiates the creation of a new config file, using `TASK_NAME` as its identifier.
* `-o FILEPATH`: (Optional) Specifies the output filename for your config. If omitted, the file will be named `task_name.json` (e.g., `my_first_git_task.json`) and placed in the default `~/git_automation_configs/` directory.

After creation, a file like `my_first_git_task.json` will appear. You'll need to **edit it** to fit your project:

```json
{
  "name": "My First Git Task",
  "origin": "origin",
  "branch": "main",
  "git_repo_path": "/path/to/your/local_git_repo", // <-- IMPORTANT: Update this path!
  "command_line": "echo 'Your command here (e.g., npm run build, python script.py)'", // <-- Update this command!
  "git_commit_message": "Automated update for My First Git Task"
=======
* **Python 3.x** installed on your system.  
* **Git** installed and configured (ensure the git command is accessible in your system's PATH).  
* A **local Git repository** ready for automation.

### **Installation**

1. **Clone this repository** (or simply copy the files) to your local machine:  
   git clone https://github.com/tugapse/gitbackup.git 
   cd gitbackup

2. Verify your file structure:  
   Your project should be organized like this:  
   gitbackup/  
   ├── main.py  
   ├── config.json  \# Or your custom config file name  
   └── core/  
        ├── \_\_init\_\_.py  
        ├── cli\_parser.py  
        ├── command\_logic.py  
        ├── git\_logic.py  
        └── logger.py

## **🛠️ Configuration**

The script uses straightforward JSON files to define each automated task.

### **Creating a New Configuration File**

You can generate a new configuration file with default settings right from your terminal:  
python main.py \--create "My First Git Task" \-o my\_task.json

* \--create "TASK\_NAME": This initiates the creation of a new config file, using TASK\_NAME as its identifier.  
* \-o my\_task.json: (Optional) Specifies the output filename for your config. If you omit this, the file will be named task\_name.json (e.g., my\_first\_git\_task.json).

After creation, a file like my\_task.json will appear. You'll need to **edit it** to fit your project:  
// my\_task.json  
{  
  "name": "My First Git Task",  
  "origin": "origin",  
  "branch": "main",  
  "git\_repo\_path": "/path/to/your/local\_git\_repo", // \<-- IMPORTANT: Update this path\!  
  "command\_line": "echo 'Your command here (e.g., npm run build, python script.py)'", // \<-- Update this command\!  
  "git\_commit\_message": "Automated update for My First Git Task"  
}
```

#### **Overwriting Existing Configs**

By default, the script prevents overwriting an existing configuration file. To force an overwrite, use the `--overwrite` flag:
```bash
python main.py --create "My Config" -o my_config.json --overwrite
```

#### **Pre-populating Fields During Creation**

You can also pre-populate fields like branch, origin, and git_repo_path when creating the file:
```bash
python main.py --create "Dev Branch Workflow" -o dev_workflow.json --branch develop --origin my-fork --folder "/home/user/my_dev_project" --verbose
```

This command creates `dev_workflow.json` with `develop` as the branch, `my-fork` as the origin, and `"/home/user/my_dev_project"` as the repository path. It also enables verbose output during the creation process itself.

### **Editing Your Configuration (--edit)**

To quickly open an existing configuration file in your system's default text editor:
```bash
python main.py my_daily_backup --edit
```
Or:
```bash
python main.py --json /path/to/my_custom_config.json --edit
```

### **Listing All Configured Tasks (--list)**

To see a summary of all configuration files found in your default config directory (`~/git_automation_configs/`):
```bash
python main.py --list
```

**Example Output:**
```
Listing all configured tasks in '/home/user/git_automation_configs':
- My First Git Task - main
  /path/to/your/local_git_repo
- Dev Branch Workflow - develop
  /home/user/my_dev_project
```

### **Key Configuration Fields**

Open your generated JSON file (e.g., `my_first_git_task.json`) and carefully **modify these key fields**:

* `name`: A clear, descriptive name for your automation task.
* `origin`: The name of your Git remote (e.g., `origin`, `upstream`). Defaults to `origin`.
* `branch`: The specific Git branch you want the script to operate on (e.g., `main`, `develop`, `feature/new-feature`). Defaults to `main`.
* `git_repo_path`: **REQUIRED!** The **absolute path** to your local Git repository. This is vital for the script to locate and manage your code.
* `command_line`: The shell command to execute *before* the Git operations. This is perfect for running build scripts, tests, data generation, or any other pre-commit steps. Leave it empty (`""`) if no command is needed.
* `git_commit_message`: The default commit message to use for automated commits. A timestamp `[MMDDHHMMSS]` will be automatically appended to this message during the commit.

## **🚀 Usage**

To run your automated task, simply specify the task name (if in the default config directory) or the full path to its configuration file:
```bash
python main.py my_daily_backup
```
Or:
```bash
python main.py --json /path/to/my_custom_config.json
```

### **Command-line Overrides**

You can temporarily override configuration values for a single run directly from the command line without modifying your JSON file. This is great for flexible execution.

* **Override Branch**:
  ```bash
  python main.py my_task.json --branch feature/experimental
  ```
* **Override Origin**:
  ```bash
  python main.py my_task.json --origin specific-remote
  ```
* **Override Repository Folder**:
  ```bash
  python main.py my_task.json --folder "/another/path/to/your/repo"
  ```
* **Combine Multiple Overrides**:
  ```bash
  python main.py my_task.json --branch hotfix/bug-fix --origin fork-origin --folder "/tmp/my_cloned_repo"
  ```

### **Initializing a Git Repository (--initialize)**

If the `git_repo_path` specified in your config (or via `--folder`) does not contain an initialized Git repository, you can tell the script to initialize it automatically:
```bash
python main.py my_new_repo_task --folder /tmp/my_new_repo --initialize --branch dev --origin https://github.com/user/new-repo.git
```
If `--initialize` is used and the repository already exists, the script will simply proceed without re-initializing it.

## **📝 Logging and Verbosity**

The script provides clear, color-coded output to suit your needs:

* **Default Output**: By default, the script provides a concise overview, showing major process steps (in **cyan**), successful completions (in **green**), and critical errors (in **red**). Informational messages (like listing tasks) are always visible.
  ```bash
  python main.py my_task.json
  ```

  **Example Output (Default):**
  ```
  Starting automated task from '/home/user/git_automation_configs/my_task.json'

  Task Details: My First Git Task
    Git Repo Path: '/home/user/Code/my-repo' (from config)
    Branch: 'main' (from config/default)
    Origin: 'origin' (from config/default)
    Command Line: 'echo "hello"'
    Git Commit Message: 'Automated update for My First Git Task'

  Performing initial Git Pull
  Initial Git Pull completed successfully.
  Executing command_line
  Command execution completed successfully.
  Checking for changes in Git Repository
  Changes detected. Performing Git Add and Commit
  Git Add and Commit completed successfully.
  Commits made. Performing Git Push
  Git Push completed successfully.
  Performing final Git Pull (post-push sync)
  Final Git Pull completed successfully.
  Task 'My First Git Task' completed successfully!
  ```

* **Verbose Mode (--verbose)**: For detailed diagnostics or to see every operation in action, use the `--verbose` flag. This will display all internal logs, including Git command outputs (STDOUT/STDERR) and extensive progress messages.
  ```bash
  python main.py my_task.json --verbose
  ```

## **📦 Building Standalone Executables**

You can package your Python script into a standalone executable for easier distribution using **PyInstaller**.

1. **Ensure PyInstaller is installed** in your virtual environment: `pip install pyinstaller`
2. **Use the provided build scripts**:
   * **For Linux/macOS**: `./build.sh`
   * **For Windows**: `build.cmd`
**Important Note on Cross-Compilation**: PyInstaller is not a cross-compiler. To create a Windows executable (.exe), you must run the build process on a Windows machine. Similarly, to create a Linux executable, build it on a Linux machine. Using virtual machines is a common way to achieve builds for different operating systems from a single host.

## **🐛 Troubleshooting**

* **Error: 'git' command not found**: This usually means Git isn't installed on your system, or its executable isn't added to your system's PATH.
* **Error: ... 'git_repo_path' is missing**: Verify that the `git_repo_path` field is correctly set in your JSON configuration file, or that you've provided it via the `--folder` command-line argument.
* **Error: ... not a valid Git repository**: The path you've provided for `git_repo_path` (or `--folder`) either doesn't exist or isn't a recognized Git repository. Use `--initialize` if you want the script to set it up for you.
* **Error: Default editor command not found**: When using `--edit`, your system needs to have a default program associated with opening `.json` files, and that program's command needs to be in your system's PATH. For Linux, ensure `xdg-open` is available.

=======
### **Creating a Configuration File with All Arguments**

You can also pre-populate fields like branch, origin, and git\_repo\_path when creating the file:  
python main.py \--create "Dev Branch Workflow" \-o dev\_workflow.json \\  
  \--branch develop \--origin my-fork \--folder "/home/user/my\_dev\_project" \--verbose

This command creates dev\_workflow.json with develop as the branch, my-fork as the origin, and "/home/user/my\_dev\_project" as the repository path. It also enables verbose output during the creation process itself.

### **Editing Your Configuration**

Open your generated JSON file (e.g., my\_task.json) and carefully **modify these key fields**:

* **name**: A clear, descriptive name for your automation task.  
* **origin**: The name of your Git remote (e.g., origin, upstream). Defaults to origin.  
* **branch**: The specific Git branch you want the script to operate on (e.g., main, develop, feature/new-feature). Defaults to main.  
* **git\_repo\_path**: **REQUIRED\!** The **absolute path** to your local Git repository. This is vital for the script to locate and manage your code.  
* **command\_line**: The shell command to execute *before* the Git operations. This is perfect for running build processes, tests, data generation, or any other pre-commit actions. Leave it empty ("") if no command is needed.  
* **git\_commit\_message**: The default commit message to use for automated commits.

## **🚀 Usage**

To run your automated task, simply specify the path to its configuration file:  
python main.py my\_task.json

### **Command-line Overrides**

You can temporarily override configuration values for a single run directly from the command line without modifying your JSON file. This is great for flexible execution.

* **Override Branch**:  
  python main.py my\_task.json \--branch feature/experimental

* **Override Origin**:  
  python main.py my\_task.json \--origin specific-remote

* **Override Repository Folder**:  
  python main.py my\_task.json \--folder "/another/path/to/your/repo"

* **Combine Multiple Overrides**:  
  python main.py my\_task.json \--branch hotfix/bug-fix \--origin fork-origin \--folder "/tmp/my\_cloned\_repo"

* **Run with Overrides and Verbose Output**:  
  python main.py my\_task.json \--branch production \--folder "/var/www/my-app" \--verbose

## **📝 Logging and Verbosity**

The script offers two distinct levels of output to suit your needs:

* **Default (Concise Output)**: By default, the script provides a clean overview, showing only the major "Step" messages and critical errors. This is ideal for routine operations where you only need to confirm success or identify high-level failures.  
  python main.py my\_task.json

  **Example Output (Default):**  
  \--- Starting automated task from 'my\_task.json' \---

  \--- Step 1: Performing initial Git Pull \---

  \--- Step 2: Executing command\_line \---

  \--- Step 3: Checking for changes in Git Repository \---

  \--- Step 4: Changes detected. Performing Git Add and Commit \---

  \--- Step 5: Commits made. Performing Git Push \---

  \--- Step 6: Performing final Git Pull (post-push sync) \---

  \--- Task 'My First Git Task' completed successfully\! \---

* **Verbose Mode**: For detailed diagnostics, debugging, or simply to see every operation in action, use the \--verbose flag. This will display all internal logs, including Git command outputs (STDOUT/STDERR) and extensive progress messages.  
  python main.py my\_task.json \--verbose

  **Example Output (Verbose \- abbreviated):**  
  \--- Starting automated task from 'my\_task.json' \---

  Task Details: My First Git Task  
    Git Repo Path: '/home/user/Code/my-repo' (from config)  
    Branch: 'main' (from config/default)  
    Origin: 'origin' (from config/default)  
    Pre-commit Command: 'echo "hello"'  
    Git Commit Message: 'Automated update for My First Git Task'  
  \------------------------------------------------------------

  \--- Step 1: Performing initial Git Pull \---  
    \[My First Git Task\] Pulling updates for branch 'main'...  
    \[My First Git Task\] Executing Git command: git pull origin main in '/home/user/Code/my-repo'  
    \[My First Git Task\] Git STDOUT:  
  Already up to date.  
    \[My First Git Task\] Git Pull successful.

  \--- Step 2: Executing command\_line \---  
    \[My First Git Task\] Attempting to execute command: 'echo "hello"'  
    \[My First Git Task\] Command STDOUT:  
  hello  
    \[My First Git Task\] Command executed successfully.  
  ... (and so on for all steps, including Git STDOUT/STDERR details)

## **⚙️ Workflow Explained**

The script executes a well-defined, sequential workflow for each task:

1. **Initial Git Pull**: Starts by performing a git pull on your specified branch to ensure your local repository is completely up-to-date.  
2. **Execute Pre-commit Command**: Runs the shell command defined in your command\_line configuration. This is where you'd typically integrate build scripts, tests, or any other necessary pre-commit steps.  
3. **Check for Changes**: Scans your Git repository for any modifications, new files, or deletions using git status \--porcelain.  
4. **Git Add & Commit**: If the script detects any changes in Step 3, it stages all modified and untracked files (git add .) and then creates a new commit using the git\_commit\_message from your configuration.  
5. **Git Push**: If a new commit was successfully created in Step 4, the script pushes your local commits to the remote repository.  
6. **Final Git Pull**: Performs one last git pull after the push. This ensures your local repository is fully synchronized with the remote, accounting for any potential concurrent changes or merge resolutions.

## **🐛 Troubleshooting**

* **Error: 'git' command not found**: This usually means Git isn't installed on your system, or its executable isn't added to your system's PATH.  
* **Error: ... 'git\_repo\_path' is missing**: Verify that the git\_repo\_path field is correctly set in your JSON configuration file, or that you've provided it via the \--folder command-line argument.  
* **Error: ... not a valid Git repository**: The path you've provided for git\_repo\_path (or \--folder) either doesn't exist or isn't a recognized Git repository.  

