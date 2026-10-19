# gitb (Git Backup & Sync)

A small CLI helper to automate pulling, committing, and pushing across personal repositories using JSON task presets.

## Setup
```bash
git clone https://github.com/tugapse/gitbackup.git
cd gitbackup
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

Run via wrapper scripts:
- Windows: .\run.cmd or .\run.ps1
- Linux/macOS: ./run.sh

## Quick Start

# 1. Create a task config
```bash
./run.cmd --create my_project --folder "C:\dev\my-app" --branch main

# 2. Run the sync (pull -> commit -> push)
./run.cmd my_project

# 3. Pull updates cleanly (auto stashes/restores local work)
./run.cmd my_project --update
```
## Usage
```bash
gitb <task> [options]
gitb [command]

Commands:
  --list                      List all saved tasks
  --create <name>             Create a new task JSON config
  --edit <task>               Open task JSON in default editor
  --fix-json                  Validate/repair config files

Git Actions:
  <task> --update                  Pull remote changes safely (stash -> pull -> pop)
  <task> --show-last-commits <n>   View last N remote commits
  <task> --revert-commit <hash>    Revert a specific commit with confirmation

Options:
  -f, --folder <path>         Override repo folder path
  -b, --branch <name>         Override git branch
  --json <path>               Run directly from a JSON file path
  --config-dir <dir>          Use a custom configs directory
  --overwrite                 Allow overwriting when creating task
  -v, --verbose               Print verbose command output
  -h, --help                  Show CLI help

## Task Config

Configs are saved as <task_name>.json under your OS app data / config folder (or --config-dir):

{
  "name": "my_project",
  "folder": "C:/dev/my-app",
  "branch": "main",
  "origin": "https://github.com/user/my-app.git",
  "pull_before_command": true,
  "pre_command": "",
  "commit_message": "sync changes",
  "push_after_command": true,
  "post_command": "",
  "timestamp_format": "%Y-%m-%d %H:%M:%S"
}
```

- Hooks: pre_command runs before staging; post_command runs after pushing.
- Timestamp: Formats appended to commit_message. Set to "" to omit.