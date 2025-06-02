from datetime import datetime
import os
import sys
# from core.messages import MESSAGES # No longer needed directly in logger.py

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
    except IOError as e:
        print(f"Error: Failed to clear log file {log_file_path}: {e}")


def log(message, level='info', task_name=""):
    """
    Logs a message to stdout and a log file, respecting verbosity settings and adding color.
    
    Args:
        message (str): The message to log.
        level (str): The log level ('debug', 'info', 'normal', 'step', 'success', 'warning', 'error', 'critical').
        task_name (str): Optional name of the task, only used for log file consistency now.
    """
    global _verbose_enabled
    
    # Define which levels are displayed by default (without --verbose)
    default_display_levels = ['info', 'step', 'normal', 'success', 'warning', 'error', 'critical']

    # Determine if this message should be displayed to the console
    # Debug messages only show if verbose is enabled
    display_to_console = _verbose_enabled or (level in default_display_levels and level != 'debug')
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # --- Construct message for CONSOLE ---
    # The 'message' parameter directly contains any icons or specific phrasing.
    console_message = message
    
    # Determine color for console output
    color_map = {
        'debug': Colors.GRAY,
        'info': Colors.BLUE,
        'normal': Colors.RESET,
        'step': Colors.CYAN,
        'success': Colors.GREEN,
        'warning': Colors.YELLOW,
        'error': Colors.RED + Colors.BOLD, # Make errors bold
        'critical': Colors.RED + Colors.BOLD # Critical errors also bold red
    }
    color_code = color_map.get(level, Colors.RESET)
    
    # Print to console only if allowed by verbosity settings, with color
    if display_to_console:
        print(f"{color_code}{console_message}{Colors.RESET}")

    # --- Construct message for LOG FILE ---
    # The log file will contain: TIMESTAMP | LEVEL | [TASK_NAME] | RAW_MESSAGE
    log_level_upper = level.upper()
    task_prefix = f"[{task_name}] " if task_name else ""
    log_line_to_file = f"{timestamp} | {log_level_upper} | {task_prefix}{message}" 

    # Always write to log file, regardless of console display settings
    log_file_path = get_log_file_path()
    try:
        with open(log_file_path, 'a') as f:
            f.write(log_line_to_file + '\n')
    except IOError as e:
        print(f"Error: Failed to write to log file {log_file_path}: {e}")