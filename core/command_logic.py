import subprocess
import os
from core.logger import log
from core.messages import MESSAGES

def execute_command(command_line, task_name="", cwd=None):
    """
    Executes a shell command.
    
    Args:
        command_line (str): The command string to execute.
        task_name (str): The name of the task for logging purposes.
        cwd (str): The current working directory for the command.
    
    Returns:
        bool: True if the command executed successfully, False otherwise.
    """
    if not command_line:
        log(MESSAGES["command_no_command_line"], level='debug', task_name=task_name)
        return True # No command to execute is considered a success

    log(MESSAGES["command_executing"].format(command_line), level='normal', task_name=task_name)
    try:
        # Use shell=True for complex commands with pipes, redirects etc.
        # Ensure proper error handling and output capture
        result = subprocess.run(
            command_line,
            shell=True,
            check=False, # We check returncode manually
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.stdout:
            for line in result.stdout.strip().splitlines():
                log(MESSAGES["command_stdout"].format(line), level='debug', task_name=task_name)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                log(MESSAGES["command_stderr"].format(line), level='debug', task_name=task_name)

        if result.returncode != 0:
            log(MESSAGES["command_failed"].format(result.returncode), level='error', task_name=task_name)
            return False
        
        log(MESSAGES["command_success"], level='success', task_name=task_name)
        return True

    except FileNotFoundError:
        log(MESSAGES["command_error_not_found"].format(command_line.split()[0]), level='error', task_name=task_name)
        return False
    except Exception as e:
        log(MESSAGES["command_unexpected_error"].format(e), level='error', task_name=task_name)
        return False    