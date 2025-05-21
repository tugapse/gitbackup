@echo off
REM This script automates Git operations: pull, add, commit, and push.
REM It intelligently checks for local changes before attempting a commit.
REM It supports a --pull argument for pull-only operations.

REM --- Configuration Variables ---
REM Set the repository location. Can be overridden by the first command-line argument.
REM %1 refers to the first command-line argument.
set "location=%1"
REM Define the target branch name for pull and push operations.
set "branch_name=master"
REM Flag to determine if only a Git pull operation should be performed.
REM Initialized to 'false' and set to 'true' if '--pull' argument is provided.
set "do_pull=false"

REM --- Color Codes for Enhanced Output Readability ---
REM ANSI escape codes for colors. Note: These may not work in older Windows Command Prompt versions.
REM For full color support, use Windows Terminal or PowerShell.
set "GREEN="
set "RED="
set "NC="
REM To enable ANSI colors in cmd.exe (Windows 10+), you might need to enable Virtual Terminal Processing:
REM reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f
REM Or use PowerShell/Windows Terminal. For this script, we'll assume a capable terminal.
REM set "GREEN=c[0;32m"
REM set "RED=c[0;31m"
REM set "NC=c[0m"


REM --- Argument Parsing ---
REM Check if the second argument is '--pull'.
REM If so, set the do_pull flag and clear the second argument.
if /i "%2"=="--pull" (
    set "do_pull=true"
)

REM --- Determine Current Script Directory ---
REM This ensures the script can find its own location robustly,
REM even if called from a different working directory.
REM %~dp0 expands to the drive letter and path of the script.
for %%i in ("%~dp0") do set "current_dir=%%~fi"

REM --- Change to Repository Directory ---
REM Prioritize the 'location' provided via argument.
REM If no location is provided, default to the script's own directory.
if not "%location%"=="" (
    REM Attempt to change to the specified repository directory.
    REM /d switch changes drive in addition to directory.
    cd /d "%location%" || (
        echo %RED%Error: Could not change to directory: %location%%NC% 1>&2
        exit /b 1 REM Exit with a non-zero status to indicate failure.
    )
) else (
    REM Attempt to change to the script's current directory.
    cd /d "%current_dir%" || (
        echo %RED%Error: Could not change to directory: %current_dir%%NC% 1>&2
        exit /b 1 REM Exit with a non-zero status to indicate failure.
    )
)

REM --- Perform Git Pull (if --pull argument is present) ---
if "%do_pull%"=="true" (
    REM Execute 'git pull'.
    REM Output is redirected to 'git_log.txt' in the current working directory.
    REM 2>&1 redirects standard error to standard output before piping.
    git pull origin "%branch_name%" >> "git_log.txt" 2>&1
    REM Inform the user that the pull operation is complete.
    echo %GREEN%Git pull operation completed.%NC%
    exit /b 0 REM Exit the script immediately after a pull-only operation.
)

REM --- Check for Uncommitted Changes (Staged or Unstaged Tracked Files) ---
REM This block uses 'git diff-index --quiet HEAD --' to reliably detect
REM any changes in tracked files (modified, added, deleted, etc.),
REM whether they are staged or unstaged.
REM The exit code (%errorlevel%) of 'git diff-index' determines if changes were found:
REM   0: No differences (no changes)
REM   1: Differences found (changes exist)
git diff-index --quiet HEAD --
if not %errorlevel% equ 0 (
    set "has_diffs=true"
) else (
    set "has_diffs=false"
)

REM --- Add, Commit, and Push Changes (if changes are detected) ---
if "%has_diffs%"=="true" (
    REM Inform the user that changes have been detected.
    echo %YELLOW%Changes detected. Adding and committing...%NC%

    REM Stage all changes in the current directory.
    git add . >> "git_log.txt" 2>&1

    REM Generate a unique timestamp for the commit message.
    REM Uses WMIC to get local date/time and formats it.
    for /f "usebackq tokens=1 delims=" %%a in (`wmic OS Get LocalDateTime /Format:List`) do (
      for /f "tokens=2 delims==" %%b in ("%%a") do (
        set "timestamp=%%b"
        REM Format: YYYYMMDD_HHMMSS
        set "timestamp=%timestamp:~0,4%%timestamp:~4,2%%timestamp:~6,2%_%timestamp:~8,2%%timestamp:~10,2%%timestamp:~12,2%"
      )
    )
    set "commit_message=Auto-commit_%timestamp%"

    REM Perform the Git commit.
    git commit -m "%commit_message%" >> "git_log.txt" 2>&1

    REM Check the exit status of the 'git commit' command.
    if %errorlevel% equ 0 (
        REM If commit was successful, attempt to push.
        git push origin "%branch_name%" >> "git_log.txt" 2>&1
        REM Check the exit status of the 'git push' command.
        if %errorlevel% equ 0 (
            echo %GREEN%Successfully pushed to origin %branch_name%.%NC%
        ) else (
            echo %RED%Error: Push failed!%NC% 1>&2
            exit /b 1 REM Exit with a non-zero status.
        )
    ) else (
        REM If commit failed, print an error and exit.
        echo %RED%Error: Commit failed!%NC% 1>&2
        exit /b 1 REM Exit with a non-zero status.
    )
) else (
    REM If no changes were detected, inform the user and skip commit/push.
    echo %YELLOW%No changes detected. Skipping commit.%NC%
)

exit /b 0 REM Exit with a zero status to indicate successful execution.
