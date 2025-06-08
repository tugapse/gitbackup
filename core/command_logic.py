# core/command_logic.py

import subprocess
import os
import sys
from core.logger import log
from core.messages import MESSAGES

def execute_command(command, task_name="", cwd=None, capture_output=False): # ADDED capture_output=False
    """
    Executes a shell command and logs its output.
    Returns: (stdout: str, success: bool) if capture_output is True,
             (None, success: bool) if capture_output is False.
    """
    if not command:
        log(MESSAGES["command_no_command_specified"], level='normal', task_name=task_name)
        return (None, True) # Consider no command as a success, nothing to do

    log(MESSAGES["command_executing"].format(command), level='normal', task_name=task_name)

    if cwd and not os.path.isdir(cwd):
        log(MESSAGES["command_error_cwd_not_exist"].format(cwd), level='error', task_name=task_name)
        return (None, False)

    try:
        # Determine how to capture output
        stdout_dest = subprocess.PIPE if capture_output else None
        stderr_dest = subprocess.PIPE if capture_output else None

        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True, # Execute command via shell
            capture_output=capture_output, # Use the passed capture_output flag
            text=True, # Ensure output is decoded as text
            check=False # Do not raise CalledProcessError automatically
        )

        output_stdout = result.stdout.strip() if result.stdout else ""
        output_stderr = result.stderr.strip() if result.stderr else ""

        if output_stdout:
            log(MESSAGES["command_stdout"].format(output_stdout), level='debug', task_name=task_name)
        if output_stderr:
            log(MESSAGES["command_stderr"].format(output_stderr), level='debug', task_name=task_name)

        if result.returncode != 0:
            log(MESSAGES["command_failed_exit_code"].format(result.returncode), level='error', task_name=task_name)
            return (output_stdout, False) # Return output even on failure if captured
        
        log(MESSAGES["command_execution_successful"], level='debug', task_name=task_name)
        return (output_stdout, True)

    except FileNotFoundError:
        log(MESSAGES["command_error_not_found"].format(command.split()[0]), level='error', task_name=task_name)
        return (None, False)
    except Exception as e:
        log(MESSAGES["command_unexpected_error"].format(e), level='error', task_name=task_name)
        return (None, False)