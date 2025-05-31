# core/command_logic.py

import subprocess
import os
from core.logger import log
from core.messages import MESSAGES

def execute_command(command, task_name=None, cwd=None):
    """
    Executes a given shell command.

    Args:
        command (str): The shell command to execute.
        task_name (str, optional): The name of the task for logging purposes. Defaults to None.
        cwd (str, optional): The current working directory for the command. Defaults to None (current script's CWD).

    Returns:
        bool: True if the command executed successfully, False otherwise.
    """
    if not command:
        log(MESSAGES["command_no_command_specified"], level='normal', task_name=task_name)
        return True

    log(MESSAGES["command_executing"].format(command), level='normal', task_name=task_name)
    
    if cwd and not os.path.isdir(cwd):
        log(MESSAGES["command_error_cwd_not_exist"].format(cwd), level='error', task_name=task_name)
        return False

    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )

        if process.stdout:
            log(MESSAGES["command_stdout"].format(process.stdout.strip()), level='normal', task_name=task_name)
        if process.stderr:
            log(MESSAGES["command_stderr"].format(process.stderr.strip()), level='normal', task_name=task_name)

        if process.returncode != 0:
            log(MESSAGES["command_failed_exit_code"].format(process.returncode), level='error', task_name=task_name)
            return False
        
        log(MESSAGES["command_execution_successful"], level='normal', task_name=task_name)
        return True

    except FileNotFoundError:
        log(MESSAGES["command_error_not_found"].format(command.split(' ')[0]), level='error', task_name=task_name)
        return False
    except Exception as e:
        log(MESSAGES["command_unexpected_error"].format(e), level='error', task_name=task_name)
        return False