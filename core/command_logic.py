# core/command_logic.py

import subprocess
import os # Import os for path handling if needed, though subprocess.run handles cwd directly
from core.logger import log

def execute_command(command, task_name=None, cwd=None): # Added cwd=None to the signature
    """
    Executes a given shell command.

    Args:
        command (str): The shell command to execute.
        task_name (str, optional): The name of the task for logging purposes. Defaults to None.
        cwd (str, optional): The current working directory for the command. Defaults to None (current script's CWD).

    Returns:
        bool: True if the command executed successfully, False otherwise.
    """
    try:
        log(f"Executing command: {command}", level='normal', task_name=task_name)
        
        # Ensure cwd is a valid path if provided
        if cwd and not os.path.isdir(cwd):
            log(f"Warning: Specified command working directory '{cwd}' does not exist.", level='warning', task_name=task_name)
            # Decide if you want to proceed without setting cwd or exit.
            # For now, we'll let subprocess.run handle it, which might error if it's critical.
            # Or you could set cwd=None here to use default, or raise an error.
            # For robustness, it's better to explicitly check and potentially exit or default.
            # Let's add a robust check here:
            log(f"Error: Command working directory '{cwd}' does not exist.", level='error', task_name=task_name)
            return False

        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd # Pass the cwd argument here
        )
        if result.stdout:
            log(f"Command STDOUT:\n{result.stdout}", level='normal', task_name=task_name)
        return True
    except subprocess.CalledProcessError as e:
        log(f"Command FAILED with exit code {e.returncode}.", level='error', task_name=task_name)
        if e.stdout:
            log(f"Command STDOUT:\n{e.stdout}", level='error', task_name=task_name)
        if e.stderr:
            log(f"Command STDERR:\n{e.stderr}", level='error', task_name=task_name)
        return False
    except FileNotFoundError:
        log(f"Error: Command '{command.split()[0]}' not found.", level='error', task_name=task_name)
        return False
    except Exception as e:
        log(f"An unexpected error occurred during command execution: {e}", level='error', task_name=task_name)
        return False