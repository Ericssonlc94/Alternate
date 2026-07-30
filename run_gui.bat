@echo off
REM Abre a GUI do Severance System usando o Python do venv do projeto.
REM O diretorio de trabalho e src\ para que "-m gui" ache o pacote; o venv
REM continua na raiz, um nivel acima. Os caminhos de data/ e assets/ nao dependem
REM disso: core.get_project_root() os resolve a partir de __file__.
cd /d "%~dp0src"

if exist "..\venv\Scripts\pythonw.exe" (
    REM pythonw.exe: sem janela de console atras da interface.
    start "" "..\venv\Scripts\pythonw.exe" -m gui
) else (
    python -m gui
)
