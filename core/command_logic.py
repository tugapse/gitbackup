# core/command_logic.py

import subprocess
import os
from core.logger import log
from core.messages import MESSAGES

def execute_command(command_line, task_name="", cwd=None):
    """
    Executes a shell command.
    
    Args:
        command_line (str): The command string to execute.
        task_name (str): The name of the task for logging.
        cwd (str, optional): The current working directory for the command. Defaults to None.
    
    Returns:
        bool: True if the command executed successfully (return code 0), False otherwise.
    """
    if not command_line:
        log(MESSAGES["command_no_command_line"], level='debug', task_name=task_name)
        return True # No command to execute is considered a success

    return _run_command(command_line.split(), cwd, task_name)


def _run_command(command_parts, cwd, task_name=""):
    """
    Internal helper to run shell commands and log their output.
    Returns True on success, False on failure.
    """
    command_str = " ".join(command_parts)
    # Changed level from 'verbose' to 'debug' here
    log(MESSAGES["command_executing"].format(command_str), level='debug', task_name=task_name)

    try:
        process = subprocess.run(
            command_parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False, # We handle return code manually
            env=os.environ,
            shell=True # Use shell=True for convenience, especially if command_parts contains pipes/redirections
        )

        if process.stdout:
            # Changed level from 'verbose' to 'debug' here
            log(MESSAGES["command_stdout"].format(process.stdout.strip()), level='debug', task_name=task_name)
        if process.stderr:
            # Changed level from 'verbose' to 'debug' here
            log(MESSAGES["command_stderr"].format(process.stderr.strip()), level='debug', task_name=task_name)

        if process.returncode == 0:
            log(MESSAGES["command_success"], level='success', task_name=task_name)
            return True
        else:
            log(MESSAGES["command_failed"].format(process.returncode), level='error', task_name=task_name)
            return False

    except FileNotFoundError:
        log(MESSAGES["command_error_not_found"].format(command_parts[0]), level='error', task_name=task_name)
        return False
    except Exception as e:
        log(MESSAGES["command_unexpected_error"].format(e), level='error', task_name=task_name)
        return False