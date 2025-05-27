import subprocess

def execute_command(command_line_str, task_name="Unnamed Task"):
    """
    Executes a given command line string.
    """
    if not command_line_str:
        print(f"  No command_line specified for '{task_name}'. Skipping command execution.")
        return True # Considered successful if no command to run

    print(f"\n  Executing command for '{task_name}': '{command_line_str}'")
    try:
        result = subprocess.run(command_line_str, shell=True, check=True, capture_output=True, text=True)
        print("    Command Output (STDOUT):\n", result.stdout)
        if result.stderr:
            print("    Command Output (STDERR):\n", result.stderr)
        print(f"  Command for '{task_name}' executed successfully with exit code {result.returncode}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error: Command for '{task_name}' failed with exit code {e.returncode}.")
        print("    STDOUT:\n", e.stdout)
        print("    STDERR:\n", e.stderr)
        return False
    except FileNotFoundError:
        print(f"  Error: Command '{command_line_str.split()[0]}' not found for '{task_name}'. Ensure it's in PATH or provide full path.")
        return False
    except Exception as e:
        print(f"  An unexpected error occurred during command execution for '{task_name}': {e}")
        return False