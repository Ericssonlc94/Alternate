@echo off
REM Gera o executavel e, em seguida, o instalador do Alternate.
REM Rode com um duplo clique ou pelo terminal; funciona de qualquer diretorio.
setlocal
cd /d "%~dp0.."

echo ============================================
echo  Alternate - build do instalador
echo ============================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo        Crie com: python -m venv venv
    echo        Depois:   venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo [1/2] Gerando o executavel com PyInstaller...
"venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean packaging\severance_gui.spec
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao gerar o executavel.
    pause
    exit /b 1
)

if not exist "dist\Alternate.exe" (
    echo.
    echo [ERRO] dist\Alternate.exe nao foi produzido.
    pause
    exit /b 1
)
echo       OK: dist\Alternate.exe
echo.

echo [2/2] Compilando o instalador com o Inno Setup...
REM O Inno Setup pode estar instalado para a maquina (Arquivos de Programas) ou
REM so para o usuario (LocalAppData, que e onde o winget costuma por). Procura
REM nos tres lugares.
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe"         set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo.
    echo [AVISO] Inno Setup 6 nao encontrado.
    echo         O executavel em dist\ esta pronto e ja funciona sozinho,
    echo         mas o instalador precisa do Inno Setup:
    echo         https://jrsoftware.org/isdl.php
    echo.
    echo         Instale e rode este script de novo.
    pause
    exit /b 2
)

"%ISCC%" packaging\installer.iss
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao compilar o instalador.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Pronto. Saida em dist\
echo ============================================
dir /b dist\*.exe
echo.
pause
