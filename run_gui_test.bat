@echo off

set "VENV_PATH=.\venv"

if not exist "%VENV_PATH%\Scripts\python.exe" (
    echo Virtual environment not found!
    pause
    exit /b 1
)

"%VENV_PATH%\Scripts\python.exe" severance_system_gui.py

pause