@echo off
REM Abre a CLI do Severance System usando o Python do venv do projeto.
REM O script roda a partir de src\, entao o Python coloca essa pasta no sys.path
REM sozinho e o "import core" resolve sem PYTHONPATH.
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado. Crie com: python -m venv venv
    pause
    exit /b 1
)

echo STARTING SEVERANCE SYSTEM...
timeout /t 3 /nobreak >nul
"venv\Scripts\python.exe" "src\severance_system.py"

pause
