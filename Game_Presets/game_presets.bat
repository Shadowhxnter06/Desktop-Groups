@echo off
cd /d "%~dp0"

:: Create the venv if it doesn't exist yet
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Install/update dependencies silently
echo Installing dependencies...
venv\Scripts\pip install -r requirements.txt --quiet

:: Run the script using the venv's Python
echo Starting...
venv\Scripts\python game_presets.py