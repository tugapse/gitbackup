
# Git Automation Script

This script provides a simple yet powerful way to automate common Git operations like pulling updates, running pre-commit commands, staging, committing, and pushing changes. It's designed to be highly configurable for different projects and offers precise control over its execution and logging.

## 🚀 Getting Started

### Prerequisites

Before you dive in, make sure you have:

*   **Python 3.x** installed on your system.
*   **Git** installed and configured (ensure the git command is accessible in your system's PATH).
*   A **local Git repository** (or a path where one can be initialized) ready for automation.

### Installation

1.  **Clone this repository** (or simply copy the files) to your local machine:

    ```bash
    git clone https://github.com/your-username/your-repo-name.git # Replace with your actual repo URL
    cd your-repo-name
    ```

2.  Verify your file structure:

    Your project should be organized like this:

    ```
    your_project/
    ├── .git/
    ├── build.sh  # or build.cmd for Windows
    ├── core/
    │   └── cli_parser.py
    ├── GitAutomator.py
    └── ...other files...
    ```

3.  **Create a virtual environment** (recommended):

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    venv\Scripts\activate  # Windows
    ```

4.  **Install dependencies:**

    ```bash
    pip install pyinstaller
    ```

## ⚙️ Workflow Explained

The script executes a well-defined, sequential workflow for each task:

1.  **Repository Setup (if needed)**:
    *   If `--initialize` is used and the `git_repo_path` doesn't exist or isn't a Git repo, it will be initialized (git init) and the origin remote will be added.
    *   The script will then ensure the specified `--branch` is checked out, creating it locally if it doesn't exist and attempting to push it to the remote to set up tracking.
2.  **Initial Git Pull**: Starts by performing a git pull on your specified branch to ensure your local repository is completely up-to-date.
3.  **Execute Pre-commit Command**: Runs the shell command defined in your `command_line` configuration. This is where you'd typically integrate build scripts, tests, data generation, or any other necessary pre-commit steps.
4.  **Check for Changes**: Scans your Git repository for any modifications, new files, or deletions using `git status --porcelain`.
5.  **Git Add & Commit**: If the script detects any changes in Step 4, it stages all modified and untracked files (`git add .`) and then creates a new commit using the `git_commit_message` from your configuration. A timestamp `[MMDDHHMMSS]` will be automatically appended to the commit message.
6.  **Git Push**: If a new commit was successfully created in Step 5, the script pushes your local commits to the remote repository.
7.  **Final Git Pull**: Performs one last git pull after the push. This ensures your local repository is fully synchronized with the remote, accounting for any potential concurrent changes or merge resolutions.

## 📦 Building Standalone Executables

You can package your Python script into a standalone executable for easier distribution using **PyInstaller**.

1.  **Ensure PyInstaller is installed** in your virtual environment: `pip install pyinstaller`.
2.  **Use the provided build scripts**:
    *   **For Linux/macOS**: Run `./build.sh`
    *   **For Windows**: Run `build.cmd`

These scripts will activate your virtual environment, clean previous builds, and then run PyInstaller to create a single executable file (e.g., `dist/GitAutomator` on Linux/macOS, `dist/GitAutomator.exe` on Windows).

**Important Note on Cross-Compilation**: PyInstaller is not a cross-compiler. To create a Windows executable (`.exe`), you must run the build process on a Windows machine. Similarly, to create a Linux executable, build it on a Linux machine. Using virtual machines is a common way to achieve builds for different operating systems from a single host.

## 🐛 Troubleshooting


*   **`Error: 'git' command not found`**: This usually means Git isn't installed on your system, or its executable isn't added to your system's PATH.
*   **`Error: ... 'git_repo_path' is missing`**: Verify that the `git_repo_path` field is correctly set in your JSON configuration file, or that you've provided it via the `--folder` command-line argument.
*   **`Error: ... not a valid Git repository`**: The path you've provided for `git_repo_path` (or `--folder`) either doesn't exist or isn't a recognized Git repository. Use `--initialize` if you want the script to set it up for you.
*   **`Error: Configuration file '...' already exists. Use --overwrite to force creation.`**: This occurs when you try to create a config file with a name that already exists without using the `--overwrite` flag.
*   **`Error: Default editor command not found.`**: When using `--edit`, your system needs to have a default program associated with opening `.json` files, and that program's command needs to be in your system's PATH. For Linux, ensure `xdg-open` is available.

## ⚙️ Workflow Explained

The script executes a well-defined, sequential workflow for each task:

1.  **Repository Setup (if needed)**:

    *   If `--initialize` is used and the `git_repo_path` doesn't exist or isn't a Git repo, it will be initialized (git init) and the origin remote will be added.
    *   The script will then ensure the specified `--branch` is checked out, creating it locally if it doesn't exist and attempting to push it to the remote to set up tracking.
2.  **Initial Git Pull**: Starts by performing a git pull on your specified branch to ensure your local repository is completely up-to-date.
3.  **Execute Pre-commit Command**: Runs the shell command defined in your `command_line` configuration. This is where you'd typically integrate build scripts, tests, data generation, or any other necessary pre-commit steps.
4.  **Check for Changes**: Scans your Git repository for any modifications, new files, or deletions using `git status --porcelain`.
5.  **Git Add & Commit**: If the script detects any changes in Step 4, it stages all modified and untracked files (`git add .`) and then creates a new commit using the `git_commit_message` from your configuration. A timestamp `[MMDDHHMMSS]` will be automatically appended to the commit message.
6.  **Git Push**: If a new commit was successfully created in Step 5, the script pushes your local commits to the remote repository.
7.  **Final Git Pull**: Performs one last git pull after the push. This ensures your local repository is fully synchronized with the remote, accounting for any potential concurrent changes or merge resolutions.
