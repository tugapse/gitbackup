@echo off
setlocal enabledelayedexpansion
REM This script automates git pull, add, and commit operations on Windows.
REM It checks for local changes before committing.
REM It now accepts a --pull argument to only run git pull

REM Set the repository location (you can change this via command line)
set "location=%1"
set "branch_name=master"
set "do_pull=false"

REM Define color codes for more readable output (limited in standard cmd)
set "GREEN="
set "RED="
set "NC="

REM Parse command-line arguments
if "%2"=="--pull" (
    set "do_pull=true"
)

REM Get the current directory of the script.  This is more robust.
for /f "tokens=*" %%i in ("%~dp0") do set "current_dir=%%i"

REM Change to the repository directory
if not "%location%"=="" (
    cd /d "%location%" || (
        echo %RED%Error: Could not change to directory: %location%%NC% 1>&2
        exit /b 1
    )
) else (
    cd /d "%current_dir%" || (
        echo %RED%Error: Could not change to directory: %current_dir%%NC% 1>&2
        exit /b 1
    )
)

REM Git pull
if %do_pull%==true (
    git pull origin "%branch_name%" 2>&1 
    echo %GREEN%Git pull operation completed.%NC%
    exit /b 0
)

REM Check for uncommitted changes using git status

if "git status --porcelain".Count equ "0" (
    set "has_diffs=false"
) else (
    set "has_diffs=true"
)

REM Add and commit if there are changes
if %has_diffs%==true (
    echo %YELLOW%Changes detected. Adding and committing...%NC%
    git add . 2>&1 


REM Generate timestamp for the commit message
    for /f "usebackq tokens=1 delims=" %%a in (`wmic OS Get LocalDateTime /Format:List`) do (
      for /f "tokens=2 delims==" %%b in ("%%a") do (
        set "timestamp=%%b"
        set "timestamp=!timestamp:~0,4!!timestamp:~4,2!!timestamp:~6,2!_!timestamp:~8,2!!timestamp:~10,2!!timestamp:~12,2!"
      )
    )
    set "commit_message=Auto-commit_!timestamp!"

    git commit -m "!commit_message!" 2>&1


    if %errorlevel% equ 0 (
        git push origin "%branch_name%" 2>&1
        if %errorlevel% equ 0 (
            echo %GREEN%Successfully pushed to origin %branch_name%.%NC%
        ) else (
            echo %RED%Error: Push failed!%NC% 1>&2
            exit /b 1
        )
    ) else (
        echo %RED%Error: Commit failed!%NC% 1>&2
        exit /b 1
    )
) else (
    echo %YELLOW%No changes detected. Skipping commit.%NC%
)

echo %GREEN%Script finished.%NC%
exit /b 0