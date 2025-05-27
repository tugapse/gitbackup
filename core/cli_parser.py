import argparse
import os

def parse_arguments():
    """
    Sets up and parses command-line arguments for the application.
    Returns the parsed arguments object.
    """
    parser = argparse.ArgumentParser(
        description="Automate Git-centric workflows or create new config files."
    )

    # Create a mutually exclusive group for running a task or creating a config
    # You can either provide a config file OR use the --create option, but not both.
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "config_file",
        nargs='?', # Makes it optional if --create is used
        help="The path to the JSON configuration file for the task (required if --create is not used)."
    )
    group.add_argument(
        "--create",
        metavar="TASK_NAME",
        help="Create a new JSON configuration file with the given task name."
    )

    # Global options, applicable when running a task or creating a config
    parser.add_argument(
        "-o", "--output",
        metavar="FILEPATH",
        help="Specify the output filepath for the new configuration file (used with --create). Defaults to TASK_NAME.json in the current directory."
    )
    # New arguments for overriding Git properties
    parser.add_argument(
        "--branch",
        help="Overrides the 'branch' specified in the config file for this run or pre-fills it during creation."
    )
    parser.add_argument(
        "--origin",
        help="Overrides the 'origin' specified in the config file for this run or pre-fills it during creation."
    )
    # New argument for specifying the local Git repository folder
    parser.add_argument(
        "--folder",
        metavar="GIT_REPO_PATH",
        help="Overrides the 'git_repo_path' specified in the config file for this run or pre-fills it during creation. This should be the absolute path to your local Git repository."
    )

    return parser.parse_args()