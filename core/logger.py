# core/logger.py

from datetime import datetime
import os
from core.messages import MESSAGES

# ANSI escape codes for colors
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m" # Darker gray for debug

# Module-level variable to control verbosity
_verbose_enabled = False

def set_verbose(enabled: bool):
    """
    Sets the verbose mode for the logger.
    If enabled is True, debug messages and all other levels will be displayed.
    """
    global _verbose_enabled
    _verbose_enabled = enabled

def get_log_file_path():
    """Determines the log file path based on XDG Base Directory Specification."""
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
    if xdg_config_home:
        return os.path.join(xdg_config_home, 'git_automation', 'git_automation.log')
    else:
        # Fallback for systems not using XDG_CONFIG_HOME or for Windows
        if os.name == 'posix': # Linux, macOS, etc.
            home_dir = os.path.expanduser("~")
            return os.path.join(home_dir, '.config', 'git_automation', 'git_automation.log')
        elif os.name == 'nt': # Windows
            appdata = os.environ.get('APPDATA')
            return os.path.join(appdata, 'git_automation', 'git_automation.log')
        else:
            # Generic fallback if OS not recognized
            return os.path.join(os.getcwd(), 'git_automation.log')

def clear_log_file():
    """Clears the content of the log file."""
    log_file_path = get_log_file_path()
    log_dir = os.path.dirname(log_file_path)
    os.makedirs(log_dir, exist_ok=True) # Ensure directory exists before trying to open file

    try:
        with open(log_file_path, 'w') as f: # 'w' mode truncates the file
            f.write(f"--- Log Cleared at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        # Do NOT log this message using `log()` function, as it would cause an infinite loop
        # if log() attempts to write to the file while it's being cleared.
    except IOError as e:
        print(f"Error: Failed to clear log file {log_file_path}: {e}")


def log(message, level='info', task_name=""):
    """
    Logs a message to stdout and a log file, respecting verbosity settings and adding color.
    
    Args:
        message (str): The message to log.
        level (str): The log level ('debug', 'info', 'normal', 'step', 'success', 'warning', 'error').
        task_name (str): Optional name of the task, prepended to the log message.
    """
    global _verbose_enabled
    
    # Define which levels are displayed by default (without --verbose)
    default_display_levels = ['info', 'step', 'normal', 'success', 'warning', 'error']

    # Determine if this message should be displayed to the console
    display_to_console = _verbose_enabled or (level in default_display_levels)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine prefix based on log level
    level_map = {
        'debug': MESSAGES.get('log_level_debug', 'DEBUG'),
        'info': MESSAGES.get('log_level_info', 'INFO'),
        'normal': MESSAGES.get('log_level_normal', ''),
        'step': MESSAGES.get('log_level_step', 'STEP'),
        'success': MESSAGES.get('log_level_success', 'SUCCESS'),
        'warning': MESSAGES.get('log_level_warning', 'WARNING'),
        'error': MESSAGES.get('log_level_error', 'ERROR'),
    }
    
    prefix = level_map.get(level, level.upper())
    
    # Format the prefix for display
    if prefix:
        display_prefix = f"[{prefix}]"
    else:
        display_prefix = "" # For 'normal' level

    # Apply task name prefix
    if task_name and level != 'normal':
        formatted_message = f"[{task_name}] {display_prefix} {message}"
    else:
        formatted_message = f"{display_prefix} {message}"
    
    log_line_to_file = f"{timestamp} {formatted_message}" # Log file gets no colors

    # Determine color for console output
    color_map = {
        'debug': Colors.GRAY,
        'info': Colors.BLUE,
        'normal': Colors.RESET,
        'step': Colors.CYAN,
        'success': Colors.GREEN,
        'warning': Colors.YELLOW,
        'error': Colors.RED + Colors.BOLD, # Make errors bold
    }
    color_code = color_map.get(level, Colors.RESET) # Default to no color
    
    # Print to console only if allowed by verbosity settings, with color
    if display_to_console:
        print(f"{color_code}{formatted_message}{Colors.RESET}")

    # Always write to log file, regardless of console display settings
    log_file_path = get_log_file_path()
    try:
        with open(log_file_path, 'a') as f:
            f.write(log_line_to_file + '\n')
    except IOError as e:
        print(f"Error: Failed to write to log file {log_file_path}: {e}")