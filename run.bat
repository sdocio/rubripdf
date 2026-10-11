@echo off
rem RubriPDF launcher for Windows.
setlocal
cd /d "%~dp0"

if not defined VENV_DIR set "VENV_DIR=.venv"

rem 1) If a virtual environment is already active, use it as-is.
if defined VIRTUAL_ENV (
    python app.py
    goto :end
)

rem 2) Find a Python 3 launcher: prefer the "py" launcher, then "python".
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY (
    echo Python 3 is required. Download it from https://python.org
    pause
    exit /b 1
)

rem 3) Create the local virtual environment on first run.
if not exist "%VENV_DIR%\" (
    echo Creating virtual environment in %VENV_DIR%...
    %PY% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Could not create a virtual environment.
        pause
        exit /b 1
    )
    "%VENV_DIR%\Scripts\pip" install -q -r requirements.txt
)

"%VENV_DIR%\Scripts\python" app.py

:end
endlocal
pause
