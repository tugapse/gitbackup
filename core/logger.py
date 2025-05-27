# core/logger.py

_VERBOSE = False # This is a private global variable to store the verbosity state

def set_verbose(verbose_flag):
    """
    Sets the global verbosity level for the logger.
    This function should be called once, typically in main.py, after parsing CLI arguments.
    """
    global _VERBOSE
    _VERBOSE = verbose_flag

def log(message, level='normal', task_name=''):
    """
    Prints a message to the console based on the configured verbosity level.

    Args:
        message (str): The string message to be displayed.
        level (str): The logging level for the message.
            - 'step': For major workflow steps (e.g., "--- Step 1: ..."). Always printed.
            - 'error': For error messages. Always printed.
            - 'normal': For regular, detailed progress messages. Printed only if verbose mode is active.
        task_name (str, optional): A prefix for the message, typically the name of the task.
                                   Adds indentation and context. Defaults to ''.
    """
    prefix = ""
    if task_name:
        # Adds indentation for messages that belong to a specific task context
        prefix = f"  [{task_name}] "

    # Determine whether to print the message based on its level and the global verbosity setting
    if level == 'step' or level == 'error':
        # Step and error messages are always printed
        print(message)
    elif _VERBOSE: # <--- This is the crucial line for filtering 'normal' logs
        # Normal messages are only printed if verbose mode is enabled
        # If task_name is provided, prepend the formatted prefix
        print(f"{prefix}{message}" if task_name else message)