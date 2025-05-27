# core/logger.py

_verbose = False

# ANSI escape codes for colors
COLOR_RED = "\033[31m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m" # NEW: Green color
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
    """
    prefix = ""
    color = ""
    log_message = ""

    if task_name:
        prefix = f"[{task_name}] "

    if level == 'error':
        color = COLOR_RED
        log_message = f"{prefix}ERROR: {message}"
    elif level == 'step':
        color = COLOR_CYAN
        log_message = f"{prefix}{message}"
    elif level == 'success': # NEW: Handle 'success' level with green color
        color = COLOR_GREEN
        log_message = f"{prefix}{message}"
    elif level == 'normal':
        if not _verbose:
            return
        log_message = f"{prefix}INFO: {message}"
    else: # Fallback for any unknown level or non-verbose normal messages
        if not _verbose and level not in ['error', 'step', 'success']: # Only print if verbose or it's an always-visible level
            return
        log_message = f"{prefix}INFO: {message}"

    # Print the message with color, followed by reset to not affect subsequent output
    print(f"{color}{log_message}{COLOR_RESET}")