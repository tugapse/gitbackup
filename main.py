import os
import json
import sys
import subprocess

from core.cli_parser import parse_arguments
from core.logger import set_verbose, log
from core.messages import MESSAGES
from core.workflow_logic import run_task_workflow
from core.config_operations import create_config_file, fix_config_files, load_task_config
from core.git_logic import get_last_commits, revert_commit


def show_help():
    help_text = """
GitAutomator - Git workflow and task runner

Usage:
  gitb <task> [options]
  gitb [command]

Commands:
  --list                      List all configured tasks
  --create <name>             Create a new workflow task
  --edit <task>               Open task configuration in editor
  --fix-json                  Inspect and repair configuration files

Git Actions:
  <task> --show-last-commits <n>   Show the last N commits for task repo
  <task> --revert-commit <hash>    Revert a specific commit with confirmation

Options:
  -c, --config-dir <dir>      Custom directory for JSON configurations
  -j, --json <path>           Execute a specific JSON config file directly
  -f, --folder <path>         Override git repository working path
  -b, --branch <name>         Set repository branch
  --overwrite                 Allow overwriting when using --create
  --initialize                Initialize repository if not present
  -v, --verbose               Enable detailed logging
  -h, --help                  Show this help screen

Examples:
  gitb daily_backup
  gitb daily_backup --edit
  gitb --create "Deploy Workflow" --folder ./app
  gitb my_task --show-last-commits 5
"""
    log(help_text.strip(), level='normal')

def ensure_config_dir(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            log(MESSAGES["config_default_config_path_created"].format(directory), level='normal')
        except Exception as e:
            log(MESSAGES["config_error_creating_default_config_path"].format(directory, e), level='error')
            sys.exit(1)


def resolve_config_path(args, base_dir, required=True, error_msg_key="cli_error_no_task_or_json"):
    config_file_path = None
    if getattr(args, 'json', None):
        config_file_path = args.json
    elif getattr(args, 'task_identifier', None):
        if args.task_identifier.lower().endswith(".json"):
            config_file_path = args.task_identifier
        else:
            config_file_path = os.path.join(base_dir, f"{args.task_identifier}.json")

    if not config_file_path:
        if required:
            log(MESSAGES[error_msg_key], level='error')
            if error_msg_key == "cli_error_edit_no_args":
                log(MESSAGES["cli_edit_usage_hint"], level='normal')
            else:
                show_help()
            sys.exit(1)
        return None

    if not os.path.exists(config_file_path):
        log(MESSAGES["cli_error_config_file_not_found"].format(config_file_path), level='error')
        sys.exit(1)

    return config_file_path


def open_file_in_editor(file_path):
    log(MESSAGES["cli_attempting_open_editor"].format(file_path), level='step')
    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", file_path], check=True)
        else:
            subprocess.run(["xdg-open", file_path], check=True)
        log(MESSAGES["cli_editor_launched_success"].format(file_path), level='success')
    except FileNotFoundError as e:
        log(MESSAGES["cli_error_editor_not_found"].format(e.filename), level='error')
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        log(MESSAGES["cli_error_opening_file_editor"].format(e), level='error')
        sys.exit(1)
    except Exception as e:
        log(MESSAGES["cli_error_unexpected_opening_file"].format(e), level='error')
        sys.exit(1)


def get_repo_context(args, base_dir):
    config_file_path = resolve_config_path(
        args, 
        base_dir, 
        required=True, 
        error_msg_key="cli_error_no_task_for_git_action"
    )
    
    task = load_task_config(config_file_path)
    git_repo_path = args.folder if args.folder is not None else task.get("git_repo_path")

    if not git_repo_path:
        log(MESSAGES["workflow_error_missing_repo_path"].format(task.get('name', 'selected task')), level='error')
        sys.exit(1)

    return git_repo_path, task.get('name', os.path.basename(config_file_path))


def handle_create(args, base_dir):
    task_name = args.create
    output_filepath = args.output or os.path.join(
        base_dir, f"{task_name.replace(' ', '_').lower()}.json"
    )

    create_config_file(
        task_name,
        output_filepath,
        branch_arg=args.branch,
        origin_arg=args.origin,
        folder_arg=args.folder,
        overwrite_flag=args.overwrite
    )
    sys.exit(0)


def handle_edit(args, base_dir):
    config_file_path = resolve_config_path(
        args, 
        base_dir, 
        required=True, 
        error_msg_key="cli_error_edit_no_args"
    )
    open_file_in_editor(config_file_path)
    sys.exit(0)


def handle_list(base_dir):
    log(MESSAGES["cli_listing_tasks_in"].format(base_dir), level='step')
    entries = os.listdir(base_dir) if os.path.exists(base_dir) else []
    json_files = [f for f in entries if f.endswith(".json")]

    if not json_files:
        log(MESSAGES["cli_no_config_files_found"].format(base_dir), level='info')
        sys.exit(0)

    tasks_found = False
    for filename in json_files:
        filepath = os.path.join(base_dir, filename)
        try:
            task = load_task_config(filepath)
            task_name = task.get("name", os.path.splitext(filename)[0])
            branch = task.get("branch", "N/A")
            repo_path = task.get("git_repo_path", "N/A")

            log(f"- {task_name} ({branch})", level='info')
            log(f"  {repo_path}", level='info')
            tasks_found = True
        except KeyError as e:
            log(MESSAGES["cli_warning_missing_key"].format(filename, e), level='warning')
        except Exception as e:
            log(MESSAGES["cli_warning_unexpected_error_reading_file"].format(filename, e), level='warning')

    if not tasks_found:
        log(MESSAGES["cli_no_valid_configs_found"].format(base_dir), level='info')

    sys.exit(0)


def handle_revert(args, base_dir):
    repo_path, task_name = get_repo_context(args, base_dir)
    confirmation = input(MESSAGES["cli_revert_confirmation"].format(args.revert_commit)).strip().lower()
    
    if confirmation != 'yes':
        log(MESSAGES["cli_revert_aborted"], level='normal')
        sys.exit(0)

    revert_commit(repo_path, args.revert_commit, task_name=task_name)
    sys.exit(0)


def main():
    # Immediate check for help arguments before parser exits
    if any(arg in sys.argv[1:] for arg in ("-h", "--help")):
        show_help()
        sys.exit(0)

    args = parse_arguments()
    set_verbose(args.verbose)

    effective_config_base_dir = os.path.abspath(args.config_dir)
    ensure_config_dir(effective_config_base_dir)

    # Route specific commands
    if args.create:
        handle_create(args, effective_config_base_dir)

    if args.edit:
        handle_edit(args, effective_config_base_dir)

    if args.list:
        handle_list(effective_config_base_dir)

    if args.fix_json:
        fix_config_files(effective_config_base_dir)
        sys.exit(0)

    if args.show_last_commits is not None:
        repo_path, task_name = get_repo_context(args, effective_config_base_dir)
        get_last_commits(repo_path, args.show_last_commits, task_name=task_name)
        sys.exit(0)

    if args.revert_commit:
        handle_revert(args, effective_config_base_dir)

    # Default command: Execute task workflow
    config_file_path = resolve_config_path(
        args, 
        effective_config_base_dir, 
        required=True, 
        error_msg_key="cli_error_no_task_or_json"
    )

    task = load_task_config(config_file_path)
    run_task_workflow(args, task, config_file_path, update_mode=args.update)


    # Load the task configuration for running the workflow
    task = load_task_config(config_file_path) # Using the new helper

    # Call the extracted workflow function, passing the update flag
    run_task_workflow(args, task, config_file_path, update_mode=args.update)