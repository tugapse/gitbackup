# core/logger.py

_verbose = False

# ANSI escape codes for colors
# \033[...m is the general format for ANSI escape codes
# 31m for red foreground, 36m for cyan foreground
# 0m to reset all attributes (important!)
COLOR_RED = "\033[31m"
COLOR_CYAN = "\033[36m"
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
        log_message = f"{prefix}>{COLOR_RESET}{message}"
    elif level == 'normal':
        if not _verbose: # 'normal' messages only show if verbose is true, so skip if not
            return
        log_message = f"{prefix}INFO: {message}"
    else: # Default for any unknown level, or if 'normal' and verbose is off
        if not _verbose and level != 'error': # Only print if verbose or it's an error (which is handled above)
            return
        log_message = f"{prefix}INFO: {message}" # Fallback for other levels or non-verbose normal

    # Print the message with color, followed by reset to not affect subsequent output
    print(f"{color}{log_message}{COLOR_RESET}")