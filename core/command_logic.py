import subprocess
import sys
from core.logger import log # Import the new logger

def execute_command(command, task_name):
    """
    Executes a shell command.
    Logs command execution and output at 'normal' level, errors at 'error' level.
    """
    # This message will only show in verbose mode
    log(f"Attempting to execute command: '{command}'", level='normal', task_name=task_name)
    try:
        # Use shell=True for simple commands; for more complex, consider shell=False and command parsing
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False # We handle the return code ourselves
        )

        if process.stdout:
            # Command STDOUT will only show in verbose mode
            log(f"Command STDOUT:\n{process.stdout.strip()}", level='normal', task_name=task_name)
        if process.stderr:
            # Command STDERR will only show in verbose mode
            log(f"Command STDERR:\n{process.stderr.strip()}", level='normal', task_name=task_name)

        if process.returncode != 0:
            # Command failures are considered errors and will always be shown
            log(f"Command FAILED with exit code {process.returncode}.", level='error', task_name=task_name)
            return False
        else:
            # This message will only show in verbose mode
            log(f"Command executed successfully.", level='normal', task_name=task_name)
            return True
    except FileNotFoundError:
        log(f"Error: The command '{command.split()[0]}' was not found.", level='error', task_name=task_name)
        return False
    except Exception as e:
        log(f"An unexpected error occurred during command execution: {e}", level='error', task_name=task_name)
        return False