@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist "config.json" (
    echo Missing config.json. Copy config.example.json and update your settings.
    exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment...
    py -m venv venv 2>nul || python -m venv venv
)

if not exist "venv\\Scripts\\activate.bat" (
    echo Failed to create virtual environment. Ensure Python is installed and on PATH.
    exit /b 1
)

call "venv\\Scripts\\activate.bat"

set "PYTHON=python"
where py >nul 2>&1 && set "PYTHON=py"

%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install -r requirements.txt || (
    echo Dependency installation failed.
    exit /b 1
)

%PYTHON% -m src.main %*

endlocal
