_verbose = False

# ANSI escape codes for colors
COLOR_RED = "\033[31m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_RESET = "\033[0m"

def set_verbose(verbose_flag):
    """
    Sets the global verbosity flag.
    """
    global _verbose
    _verbose = verbose_flag

def log(message, level='normal', task_name=None):
    """
    Logs a message with a specific level and optional task name,
    applying color based on the log level.

    Levels:
    - 'error': Critical issues, always displayed, red.
    - 'step': Major steps in the workflow, always displayed, cyan.
    - 'success': Successful operations, always displayed, green.
    - 'info': Important information that should always be displayed, no special color.
    - 'normal': Debugging or detailed information, only displayed if verbose is true, no special color.
    - 'warning': Warnings, always displayed, no special color (can add yellow later if desired).
    """
    prefix = ""
    color = ""
    log_message = ""

    if task_name:
        prefix = f"[{task_name}] "

    if level == 'error':
        color = COLOR_RED
        log_message = f"{prefix}{message}"
    elif level == 'step':
        color = COLOR_CYAN
        log_message = f"{prefix}{message}"
    elif level == 'success':
        color = COLOR_GREEN
        log_message = f"{prefix}{message}"
    elif level == 'info':
        log_message = f"{prefix}{message}" # Always print info messages
    elif level == 'warning': # Added 'warning' level to always print
        log_message = f"{prefix}{message}"
    elif level == 'normal': # Only print 'normal' messages if verbose is true
        if not _verbose:
            return
        log_message = f"{prefix}{message}"
    else: # Fallback for any unknown level
        if not _verbose:
            return
        log_message = f"{prefix}{message}" # Print unknown levels if verbose

    # Print the message with color, followed by reset to not affect subsequent output
    print(f"{color}{log_message}{COLOR_RESET}")