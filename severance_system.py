import json
import subprocess
import psutil # pyright: ignore[reportMissingModuleSource]
import time
import sys
import os
import winsound
import random
import string
import pygetwindow as gw # pyright: ignore[reportMissingImports]
import shutil
import pyautogui  # pyright: ignore[reportMissingModuleSource]
import ctypes
import winreg
import tkinter as tk
from tkinter import filedialog
from rich.console import Console # pyright: ignore[reportMissingImports]
from rich.panel import Panel # pyright: ignore[reportMissingImports]
from rich.text import Text # pyright: ignore[reportMissingImports]
from rich.prompt import Prompt, Confirm # pyright: ignore[reportMissingImports]
from rich.table import Table # pyright: ignore[reportMissingImports]
from rich.live import Live # pyright: ignore[reportMissingImports]
from rich.align import Align # pyright: ignore[reportMissingImports]

# --- CONSTANTS ---
STYLE_BG = "on #001E29"
STYLE_FG = "white"
STYLE_ACCENT = "cyan"
STYLE_ERROR = "bold red"
STYLE_MATRIX = "white"
WORK_DB = "work_apps.json"
PERSONAL_DB = "personal_apps.json"
CONFIG_DB = "config.json"

console = Console(style=f"{STYLE_FG} {STYLE_BG}")

# --- I18N (Internationalization) ---
i18n = {
    'pt': {
        # General
        "work_mode": "TRABALHO",
        "personal_mode": "PESSOAL",
        "none_mode": "NENHUM",
        "error": "ERRO",
        "warning": "AVISO",
        "success": "SUCESSO",
        "confirm_yes": "Sim",
        "confirm_no": "Não",
        "confirm_prompt": "Deseja continuar?",
        "try_again_prompt": "Tentar novamente?",
        "back_to_main_menu": "Voltando ao menu principal...",
        "press_enter_to_return": "Pressione [bold]Enter[/bold] para voltar ao menu",
        "created_by": "Created by Ericsson Cardoso",
        "invalid_option": "OPÇÃO INVÁLIDA.",
        # Splash & Welcome
        "lumon_industries": "LUMON INDUSTRIES.",
        "connecting_to_mainframe": "CONECTANDO AO MAINFRAME...",
        "welcome_to_severance": "BEM-VINDO AO SISTEMA SEVERANCE",
        "what_is_your_name_innie": "Qual é o seu nome, innie?",
        "verifying_credentials": "VERIFICANDO CREDENCIAIS...",
        "access_granted": "ACESSO CONCEDIDO",
        "hello_prepared_for_new_day": "Olá, {user_name}! Preparado para um novo dia?",
        "welcome_back": "Bem-vindo de volta, {user_name}!",
        "goodbye": "Até logo, {user_name}! Tenha um bom dia.",
        "shutting_down": "DESLIGANDO SISTEMA...",
        "emergency_shutdown": "DESLIGAMENTO DE EMERGÊNCIA INICIADO.",
        # Main Menu
        "main_menu_title": "MENU DE OPÇÕES",
        "active_mode": "MODO ATIVO",
        "menu_option_1": "INICIAR MODO DE TRABALHO",
        "menu_option_2": "INICIAR MODO PESSOAL",
        "menu_option_3": "ADICIONAR APP AO BANCO DE DADOS",
        "menu_option_4": "CONSULTAR BANCO DE DADOS",
        "menu_option_5": "EXCLUIR APP DO BANCO DE DADOS",
        "menu_option_6": "ADICIONAR PAPEL DE PAREDE",
        "menu_option_7": "LIMPAR CACHE E ARQUIVOS TEMPORÁRIOS",
        "menu_option_8": "RESTAURAR AO PADRÃO",
        "menu_option_9": "SAIR",
        "change_language_prompt": "Mudar Idioma (EN/PT)",
        # Battery
        "battery_charging": "CARREGANDO",
        "battery_discharging": "DESCARREGANDO",
        "battery_na": "BATERIA N/A",
        # Process Management
        "terminating_apps": "TERMINANDO APLICATIVOS DO MODO ANTERIOR...",
        "terminated_aggressively": "TERMINADO (KILL AGRESSIVO)",
        "terminated": "TERMINADO",
        "failed_to_terminate": "FALHA AO TERMINAR",
        "processes_terminated": "{count} PROCESSOS TERMINADOS.",
        "starting_apps": "INICIANDO APLICATIVOS DO MODO ATUAL...",
        "already_running": "JÁ EM EXECUÇÃO",
        "started": "INICIADO",
        "failed_to_start": "FALHA AO INICIAR",
        "apps_launched": "{count} APLICATIVOS INICIADOS.",
        "finishing_interfaces": "FINALIZANDO INTERFACES...",
        "closing_window_alt_f4": "Fechando interface de '{title}' com Alt+F4...",
        "could_not_close_window": "Não foi possível fechar a janela de '{name}': {e}",
        "organizing_desktop": "ORGANIZANDO ÁREA DE TRABALHO...",
        "closing_window": "Fechando janela",
        "closing_regular_dropbox_window": "Fechando janela regular do Dropbox",
        "error_closing_windows": "Ocorreu um erro ao fechar as janelas: {e}",
        "windows_closed": "{count} JANELAS FECHADAS.",
        "minimizing_window": "Minimizando janela",
        "error_minimizing_windows": "Ocorreu um erro ao minimizar janelas: {e}",
        "windows_minimized": "{count} JANELAS MINIMIZADAS.",
        # Loading / Status
        "loading_data": "CARREGANDO DADOS...",
        "processing": "PROCESSANDO...",
        # System Junk
        "clearing_cache": "LIMPANDO CACHE E ARQUIVOS TEMPORÁRIOS...",
        "removed": "Removido",
        "permission_denied": "PERMISSÃO NEGADA",
        "error_removing": "ERRO AO REMOVER",
        "permission_denied_listing": "Não foi possível listar o conteúdo de: {dir}. Tente executar como administrador para limpar esta pasta.",
        "error_accessing": "ERRO AO ACESSAR",
        "temp_items_removed": "{count} ITENS TEMPORÁRIOS REMOVIDOS.",
        # Start Mode
        "starting_mode": "INICIANDO {mode_name}...",
        "wallpaper_not_found": "Arquivo de papel de parede não encontrado: {path}",
        "wallpaper_warning": "Papel de parede configurado para o modo {mode_name} não encontrado: {path}",
        "applying_wallpaper": "APLICANDO PAPEL DE PAREDE PARA O MODO {mode_name}...",
        "wallpaper_applied": "PAPEL DE PAREDE APLICADO.",
        "error_applying_wallpaper": "ERRO AO APLICAR PAPEL DE PAREDE",
        "no_wallpaper_configured": "Nenhum papel de parede configurado para o modo {mode_name}.",
        "mode_activated_successfully": "MODO {mode_name} ATIVADO COM SUCESSO.",
        # View Database
        "view_db_title": "BANCO DE DADOS DE APLICATIVOS",
        "work_mode_col": "MODO DE TRABALHO",
        "personal_mode_col": "MODO PESSOAL",
        "app_info_admin": "[bold red](Requer Admin)[/bold red]",
        # Add App
        "add_app_title": "ADICIONAR NOVO APLICATIVO",
        "select_db": "Selecione o banco de dados",
        "db_choice_work": "t",
        "db_choice_personal": "p",
        "app_name_prompt": "NOME DO APP (ex: Notepad) ou digite [0] para voltar",
        "opening_file_browser": "Abrindo buscador de arquivos...",
        "file_selected": "Caminho selecionado",
        "no_file_selected": "Nenhum arquivo selecionado. Operação cancelada.",
        "error_opening_file_browser": "Não foi possível abrir o buscador de arquivos: {e}",
        "close_after_launch_prompt": "Fechar janela após iniciar? (ex: Serpro, Steam)",
        "requires_admin_prompt": "Este aplicativo requer permissão de administrador?",
        "app_added_success": "App '{name}' adicionado.",
        "name_path_empty_error": "Nome e caminho não podem ser vazios.",
        "add_another_app_prompt": "Deseja adicionar outro aplicativo?",
        "file_dialog_executables": "Executáveis",
        "file_dialog_vbscript": "VBScript",
        "file_dialog_all_files": "Todos os arquivos",
        # Delete App
        "delete_app_title": "EXCLUIR APLICATIVO",
        "consulting_records": "CONSULTANDO REGISTROS...",
        "db_is_empty": "O banco de dados {db} está vazio.",
        "apps_in_db": "Aplicativos no banco de dados:",
        "delete_app_prompt": "Digite o NÚMERO do app que deseja excluir ou digite [0] para voltar",
        "invalid_number_prompt": "Número inválido. Por favor, digite um número entre 1 e {max}.",
        "invalid_input_prompt": "Entrada inválida. Por favor, digite um número.",
        "delete_confirm_prompt": "Tem certeza que deseja excluir '{name}'?",
        "app_deleted_success": "App '{name}' excluído.",
        "operation_cancelled": "Operação cancelada.",
        "delete_another_app_prompt": "Deseja excluir outro aplicativo?",
        # Wallpaper
        "wallpaper_config_title": "CONFIGURAR PAPEL DE PAREDE",
        "wallpaper_config_loading": "INICIANDO CONFIGURAÇÃO DE PAPEL DE PAREDE...",
        "select_mode_for_wallpaper": "Selecione o modo para configurar o papel de parede",
        "opening_file_browser_for_mode": "Abrindo buscador de arquivos para o modo {mode_name}...",
        "image_files": "Arquivos de Imagem",
        "invalid_file_format": "Formato de arquivo inválido. Apenas .jpg e .png são permitidos.",
        "select_wallpaper_style": "Selecione o estilo do papel de parede:",
        "style_fill": "Preencher (Fill)",
        "style_fit": "Ajustar (Fit)",
        "style_stretch": "Esticar (Stretch)",
        "style_tile": "Lado a Lado (Tile)",
        "style_center": "Centralizar (Center)",
        "style_span": "Span (Múltiplos Monitores)",
        "choose_option": "Escolha uma opção",
        "wallpaper_set_success": "Papel de parede para o modo {mode_name} configurado como '{style_name}'.",
        "configure_another_wallpaper_prompt": "Deseja configurar outro papel de parede?",
        # Restore
        "restore_title": "RESTAURAR AO PADRÃO",
        "restore_loading": "PREPARANDO PARA RESTAURAR PADRÕES...",
        "restore_warning": "[bold red]ATENÇÃO:[/bold red] Esta ação irá apagar TODOS os dados (aplicativos e configurações) e restaurar o sistema ao seu estado inicial. Tem certeza que deseja continuar?",
        "system_restored": "SISTEMA RESTAURADO AO PADRÃO COM SUCESSO.",
        "restart_app_prompt": "Por favor, reinicie o aplicativo para aplicar todas as mudanças.",
        "error_restoring": "ERRO AO RESTAURAR",
    },
    'en': {
        # General
        "work_mode": "WORK",
        "personal_mode": "PERSONAL",
        "none_mode": "NONE",
        "error": "ERROR",
        "warning": "WARNING",
        "success": "SUCCESS",
        "confirm_yes": "Yes",
        "confirm_no": "No",
        "confirm_prompt": "Do you want to continue?",
        "try_again_prompt": "Try again?",
        "back_to_main_menu": "Returning to main menu...",
        "press_enter_to_return": "Press [bold]Enter[/bold] to return to the menu",
        "created_by": "Created by Ericsson Cardoso",
        "invalid_option": "INVALID OPTION.",
        # Splash & Welcome
        "lumon_industries": "LUMON INDUSTRIES.",
        "connecting_to_mainframe": "CONNECTING TO MAINFRAME...",
        "welcome_to_severance": "WELCOME TO THE SEVERANCE SYSTEM",
        "what_is_your_name_innie": "What is your name, innie?",
        "verifying_credentials": "VERIFYING CREDENTIALS...",
        "access_granted": "ACCESS GRANTED",
        "hello_prepared_for_new_day": "Hello, {user_name}! Ready for a new day?",
        "welcome_back": "Welcome back, {user_name}!",
        "goodbye": "Goodbye, {user_name}! Have a nice day.",
        "shutting_down": "SHUTTING DOWN SYSTEM...",
        "emergency_shutdown": "EMERGENCY SHUTDOWN INITIATED.",
        # Main Menu
        "main_menu_title": "OPTIONS MENU",
        "active_mode": "ACTIVE MODE",
        "menu_option_1": "START WORK MODE",
        "menu_option_2": "START PERSONAL MODE",
        "menu_option_3": "ADD APP TO DATABASE",
        "menu_option_4": "VIEW DATABASE",
        "menu_option_5": "DELETE APP FROM DATABASE",
        "menu_option_6": "SET WALLPAPER",
        "menu_option_7": "CLEAR CACHE AND TEMP FILES",
        "menu_option_8": "RESTORE TO DEFAULT",
        "menu_option_9": "EXIT",
        "change_language_prompt": "Change Language (EN/PT)",
        # Battery
        "battery_charging": "CHARGING",
        "battery_discharging": "DISCHARGING",
        "battery_na": "BATTERY N/A",
        # Process Management
        "terminating_apps": "TERMINATING PREVIOUS MODE APPLICATIONS...",
        "terminated_aggressively": "TERMINATED (AGGRESSIVE KILL)",
        "terminated": "TERMINATED",
        "failed_to_terminate": "FAILED TO TERMINATE",
        "processes_terminated": "{count} PROCESSES TERMINATED.",
        "starting_apps": "STARTING CURRENT MODE APPLICATIONS...",
        "already_running": "ALREADY RUNNING",
        "started": "STARTED",
        "failed_to_start": "FAILED TO START",
        "apps_launched": "{count} APPLICATIONS LAUNCHED.",
        "finishing_interfaces": "CLOSING INTERFACES...",
        "closing_window_alt_f4": "Closing interface for '{title}' with Alt+F4...",
        "could_not_close_window": "Could not close window for '{name}': {e}",
        "organizing_desktop": "ORGANIZING DESKTOP...",
        "closing_window": "Closing window",
        "closing_regular_dropbox_window": "Closing regular Dropbox window",
        "error_closing_windows": "An error occurred while closing windows: {e}",
        "windows_closed": "{count} WINDOWS CLOSED.",
        "minimizing_window": "Minimizing window",
        "error_minimizing_windows": "An error occurred while minimizing windows: {e}",
        "windows_minimized": "{count} WINDOWS MINIMIZED.",
        # Loading / Status
        "loading_data": "LOADING DATA...",
        "processing": "PROCESSING...",
        # System Junk
        "clearing_cache": "CLEARING CACHE AND TEMPORARY FILES...",
        "removed": "Removed",
        "permission_denied": "PERMISSION DENIED",
        "error_removing": "ERROR REMOVING",
        "permission_denied_listing": "Could not list contents of: {dir}. Try running as administrator to clear this folder.",
        "error_accessing": "ERROR ACCESSING",
        "temp_items_removed": "{count} TEMPORARY ITEMS REMOVED.",
        # Start Mode
        "starting_mode": "STARTING {mode_name} MODE...",
        "wallpaper_not_found": "Wallpaper file not found: {path}",
        "wallpaper_warning": "Wallpaper configured for {mode_name} mode not found: {path}",
        "applying_wallpaper": "APPLYING WALLPAPER FOR {mode_name} MODE...",
        "wallpaper_applied": "WALLPAPER APPLIED.",
        "error_applying_wallpaper": "ERROR APPLYING WALLPAPER",
        "no_wallpaper_configured": "No wallpaper configured for {mode_name} mode.",
        "mode_activated_successfully": "{mode_name} MODE ACTIVATED SUCCESSFULLY.",
        # View Database
        "view_db_title": "APPLICATION DATABASE",
        "work_mode_col": "WORK MODE",
        "personal_mode_col": "PERSONAL MODE",
        "app_info_admin": "[bold red](Requires Admin)[/bold red]",
        # Add App
        "add_app_title": "ADD NEW APPLICATION",
        "select_db": "Select the database",
        "db_choice_work": "w",
        "db_choice_personal": "p",
        "app_name_prompt": "APP NAME (e.g., Notepad) or type [0] to go back",
        "opening_file_browser": "Opening file browser...",
        "file_selected": "File selected",
        "no_file_selected": "No file selected. Operation cancelled.",
        "error_opening_file_browser": "Could not open file browser: {e}",
        "close_after_launch_prompt": "Close window after launch? (e.g., Serpro, Steam)",
        "requires_admin_prompt": "Does this application require administrator privileges?",
        "app_added_success": "App '{name}' added successfully.",
        "name_path_empty_error": "Name and path cannot be empty.",
        "add_another_app_prompt": "Do you want to add another application?",
        "file_dialog_executables": "Executables",
        "file_dialog_vbscript": "VBScript",
        "file_dialog_all_files": "All files",
        # Delete App
        "delete_app_title": "DELETE APPLICATION",
        "consulting_records": "CONSULTING RECORDS...",
        "db_is_empty": "The {db} database is empty.",
        "apps_in_db": "Applications in database:",
        "delete_app_prompt": "Enter the NUMBER of the app to delete or type [0] to go back",
        "invalid_number_prompt": "Invalid number. Please enter a number between 1 and {max}.",
        "invalid_input_prompt": "Invalid input. Please enter a number.",
        "delete_confirm_prompt": "Are you sure you want to delete '{name}'?",
        "app_deleted_success": "App '{name}' deleted successfully.",
        "operation_cancelled": "Operation cancelled.",
        "delete_another_app_prompt": "Do you want to delete another application?",
        # Wallpaper
        "wallpaper_config_title": "CONFIGURE WALLPAPER",
        "wallpaper_config_loading": "STARTING WALLPAPER CONFIGURATION...",
        "select_mode_for_wallpaper": "Select the mode to configure the wallpaper for",
        "opening_file_browser_for_mode": "Opening file browser for {mode_name} mode...",
        "image_files": "Image Files",
        "invalid_file_format": "Invalid file format. Only .jpg and .png are allowed.",
        "select_wallpaper_style": "Select the wallpaper style:",
        "style_fill": "Fill",
        "style_fit": "Fit",
        "style_stretch": "Stretch",
        "style_tile": "Tile",
        "style_center": "Center",
        "style_span": "Span (Multiple Monitors)",
        "choose_option": "Choose an option",
        "wallpaper_set_success": "Wallpaper for {mode_name} mode set to '{style_name}'.",
        "configure_another_wallpaper_prompt": "Do you want to configure another wallpaper?",
        # Restore
        "restore_title": "RESTORE TO DEFAULT",
        "restore_loading": "PREPARING TO RESTORE DEFAULTS...",
        "restore_warning": "[bold red]WARNING:[/bold red] This action will delete ALL data (applications and settings) and restore the system to its initial state. Are you sure you want to continue?",
        "system_restored": "SYSTEM RESTORED TO DEFAULT SUCCESSFULLY.",
        "restart_app_prompt": "Please restart the application to apply all changes.",
        "error_restoring": "ERROR RESTORING",
    }
}

# --- GLOBAL CONFIG & LANG ---
config = {}
LANG = 'pt' # Default language, will be updated on load

def get_text(key, **kwargs):
    """Fetches a text from the i18n dictionary for the current language."""
    return i18n.get(LANG, i18n['pt']).get(key, f"<{key}>").format(**kwargs)

# --- DATABASE FUNCTIONS ---
def get_db_path(db_name):
    exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    os.makedirs(exe_dir, exist_ok=True)
    return os.path.join(exe_dir, db_name)

def load_apps(db_name):
    db_path = get_db_path(db_name)
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_apps(db_name, apps):
    db_path = get_db_path(db_name)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(apps, f, indent=4)

def load_config():
    config_path = get_db_path(CONFIG_DB)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} # Return empty dict to signify first run

def save_config(new_config):
    global config
    config = new_config
    config_path = get_db_path(CONFIG_DB)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

# --- PROCESS MANAGEMENT FUNCTIONS ---
def manage_processes(apps_to_launch, apps_to_terminate, status):
    # 1. IDENTIFY SHARED APPS
    launch_paths = {os.path.normcase(app['path']) for app in apps_to_launch}
    apps_to_terminate = [app for app in apps_to_terminate if os.path.normcase(app['path']) not in launch_paths]

    # 2. TERMINATION LOGIC
    status.update(f"[bold white]{get_text('terminating_apps')}[/bold white]")
    terminated_count = 0
    if apps_to_terminate:
        running_procs = list(psutil.process_iter(['pid', 'name', 'exe']))

        for app in apps_to_terminate:
            app_name_lower = app["name"].lower()

            # Aggressive termination for Dropbox
            if "dropbox" in app_name_lower:
                for p in running_procs:
                    try:
                        p_name = p.name().lower()
                        p_exe = os.path.basename(p.info['exe']).lower() if p.info['exe'] else ''
                        if "dropbox" in p_name or "dropbox" in p_exe:
                            p.kill()
                            terminated_count += 1
                            console.log(f"[dim]{get_text('terminated_aggressively')}:[/dim] {p.name()} (PID: {p.pid})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            # Standard termination for other apps
            else:
                for p in running_procs:
                    try:
                        p_exe = os.path.normcase(p.info['exe']) if p.info['exe'] else ''
                        if p_exe == os.path.normcase(app["path"]):
                            p.terminate()
                            terminated_count += 1
                            console.log(f"[dim]{get_text('terminated')}:[/dim] {app['name']} (PID: {p.pid})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        console.log(f"[{STYLE_ERROR}]{get_text('failed_to_terminate')}:[/{STYLE_ERROR}] {app['name']}")
                        continue
    
    console.log(f"[bold white]{get_text('processes_terminated', count=terminated_count)}[/bold white]")
    time.sleep(1)

    # 3. LAUNCH LOGIC
    status.update(f"[bold white]{get_text('starting_apps')}[/bold white]")
    launched_count = 0
    if apps_to_launch:
        running_app_paths = {os.path.normcase(p.info['exe']) for p in psutil.process_iter(['exe']) if p.info.get('exe')}
        for app in apps_to_launch:
            app_path = app["path"]
            app_name_lower = app["name"].lower()

            if os.path.normcase(app_path) in running_app_paths:
                console.log(f"[dim]{get_text('already_running')}:[/dim] {app['name']}")
                continue
            
            try:
                _, ext = os.path.splitext(app_path)
                requires_admin = app.get("requires_admin", False)
                work_dir = os.path.dirname(app_path)

                # Special handling for Steam
                if "steam" in app_name_lower:
                    subprocess.Popen([app_path, "-silent"], cwd=work_dir)
                    launched_count += 1
                    console.log(f"[dim]{get_text('started')}:[/dim] {app['name']}")
                
                # Admin execution
                elif requires_admin:
                    executable = "wscript.exe" if ext.lower() == ".vbs" else app_path
                    params = f'"{app_path}"' if ext.lower() == ".vbs" else None
                    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, work_dir, 1)
                    if ret > 32:
                        launched_count += 1
                        console.log(f"[dim]{get_text('started')}:[/dim] {app['name']}")
                    else:
                        raise OSError(f"ShellExecuteW failed with error code {ret}. User may have cancelled the UAC prompt.")
                
                # Standard non-admin execution
                else:
                    if ext.lower() == ".vbs":
                        subprocess.Popen(["wscript.exe", app_path], cwd=work_dir)
                    else:
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = 6
                        subprocess.Popen([app_path], startupinfo=startupinfo, cwd=work_dir)
                    launched_count += 1
                    console.log(f"[dim]{get_text('started')}:[/dim] {app['name']}")

                time.sleep(0.2)
            except Exception as e:
                console.log(f"[{STYLE_ERROR}]{get_text('failed_to_start')}:[/{STYLE_ERROR}] {app['name']} - {e}")

    console.log(f"[bold white]{get_text('apps_launched', count=launched_count)}[/bold white]")
    time.sleep(1)

    apps_to_close = [app for app in apps_to_launch if app.get("close_after_launch")]
    if apps_to_close:
        status.update(f"[bold white]{get_text('finishing_interfaces')}[/bold white]")
        time.sleep(4)
        for app in apps_to_close:
            try:
                app_name = app.get("name")
                if not app_name: continue
                windows = [w for w in gw.getAllWindows() if app_name.lower() in w.title.lower()]
                if not windows:
                    short_name = app_name.split()[0]
                    windows = [w for w in gw.getAllWindows() if short_name.lower() in w.title.lower()]
                if windows:
                    window = windows[0]
                    console.log(f"[dim]{get_text('closing_window_alt_f4', title=window.title)}[/dim]")
                    window.activate()
                    time.sleep(1)
                    pyautogui.hotkey('alt', 'f4')
                    time.sleep(0.5)
            except Exception as e:
                console.log(f"[{STYLE_ERROR}]{get_text('could_not_close_window', name=app.get('name', 'unknown'), e=e)}[/{STYLE_ERROR}]")

# --- UI FUNCTIONS ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_loading_spinner(text=None, duration=1.5):
    clear_screen()
    spinner_text = text if text is not None else get_text('loading_data')
    with console.status(spinner_text, spinner="dots"):
        time.sleep(duration)

def type_text_effect(text, style):
    for char in text:
        console.print(char, end="", style=style)
        try: winsound.Beep(1400, 20)
        except Exception: pass
        time.sleep(0.025)
    console.print()
    time.sleep(0.5)

def crypto_animation(text_to_reveal):
    chars = string.ascii_uppercase + string.digits + "!@#$%^&*"
    result = [""] * len(text_to_reveal)
    with Live(console=console, auto_refresh=False) as live:
        for i in range(len(text_to_reveal)):
            if text_to_reveal[i] == " ":
                result[i] = " "
                continue
            for _ in range(5):
                scrambled_text = list(result)
                for j in range(i, len(text_to_reveal)):
                    if text_to_reveal[j] != " ":
                       scrambled_text[j] = random.choice(chars)
                live.update(Text("".join(scrambled_text), justify="center", style="cyan"), refresh=True)
                time.sleep(0.04)
            result[i] = text_to_reveal[i]
            live.update(Text("".join(result), justify="center", style="cyan"), refresh=True)
            time.sleep(0.05)

def show_splash_screen():
    clear_screen()
    console.rule(style=STYLE_MATRIX)
    type_text_effect(get_text("lumon_industries"), style=STYLE_MATRIX)
    type_text_effect(get_text("connecting_to_mainframe"), style=STYLE_MATRIX)
    console.rule(style=STYLE_MATRIX)
    time.sleep(1)

def get_battery_status():
    try:
        battery = psutil.sensors_battery()
        if battery:
            percent = int(battery.percent)
            status_key = "battery_charging" if battery.power_plugged else "battery_discharging"
            status = get_text(status_key)
            return f"{status}: {percent}%"
        return get_text("battery_na")
    except Exception:
        return get_text("battery_na")

def show_header():
    clear_screen()
    battery_status = get_battery_status()
    top_bar = Table.grid(expand=True)
    top_bar.add_column()
    top_bar.add_column(justify="right")
    top_bar.add_row(Text("SYS_OK [/]", style=STYLE_ACCENT), Text(battery_status, style=STYLE_FG))
    console.print(top_bar)
    console.print(Panel(Text("SEVERANCE SYSTEM", justify="center", style="bold white"), style=STYLE_ACCENT, border_style=STYLE_ACCENT))
    active_mode = config.get('active_mode', get_text('none_mode'))
    console.print(Align.center(Text.from_markup(f"{get_text('active_mode')}: [bold]{active_mode}[/bold]", style="dim")))
  
def show_main_menu():
    show_header()
    console.print()
    menu_options = [
        ("1", get_text("menu_option_1")),
        ("2", get_text("menu_option_2")),
        ("3", get_text("menu_option_3")),
        ("4", get_text("menu_option_4")),
        ("5", get_text("menu_option_5")),
        ("6", get_text("menu_option_6")),
        ("7", get_text("menu_option_7")),
        ("8", get_text("menu_option_8")),
        ("9", get_text("menu_option_9")),
    ]
    max_desc_len = max(len(desc) for _, desc in menu_options)
    fixed_dots_length = 19
    formatted_lines = [f"[{num}]{'.' * fixed_dots_length} {desc.ljust(max_desc_len)}" for num, desc in menu_options]
    menu_text = "\n".join(formatted_lines)
    
    lang_switcher_text = Text.from_markup(f"[[*]] {get_text('change_language_prompt')}", style="dim")
    
    console.print(Panel(Align.center(Text(menu_text)), title=get_text("main_menu_title"), border_style=STYLE_FG, padding=(2, 4)))
    
    bottom_grid = Table.grid(expand=True)
    bottom_grid.add_column()
    bottom_grid.add_column(justify="center")
    bottom_grid.add_row(
        Align.center(Text(get_text("created_by"), style="dim")),
        lang_switcher_text
    )
    console.print(bottom_grid)

def clear_system_junk(console):
    console.log(f"[bold white]{get_text('clearing_cache')}[/bold white]")
    temp_dirs = [os.environ.get('TEMP'), os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Temp')]
    cleaned_count = 0
    for temp_dir in temp_dirs:
        if not temp_dir or not os.path.exists(temp_dir): continue
        try:
            for item_name in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item_name)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    cleaned_count += 1
                    console.log(f"[dim]{get_text('removed')}:[/dim] {item_path}")
                except PermissionError:
                    console.log(f"[{STYLE_ERROR}]{get_text('permission_denied')}:[/{STYLE_ERROR}] {item_path}")
                except OSError as e:
                    console.log(f"[{STYLE_ERROR}]{get_text('error_removing')}:[/{STYLE_ERROR}] {item_path} - {e}")
        except PermissionError:
            console.log(f"[{STYLE_ERROR}]{get_text('permission_denied')}:[/{STYLE_ERROR}] {get_text('permission_denied_listing', dir=temp_dir)}")
        except OSError as e:
            console.log(f"[{STYLE_ERROR}]{get_text('error_accessing')}:[/{STYLE_ERROR}] {temp_dir} - {e}")
    console.log(f"[bold white]{get_text('temp_items_removed', count=cleaned_count)}[/bold white]")
    time.sleep(1)

def start_mode(mode_name, apps_to_launch, apps_to_terminate):
    show_loading_spinner(get_text('starting_mode', mode_name=mode_name))
    
    current_config = config.copy()
    current_config['active_mode'] = mode_name
    save_config(current_config)

    wallpaper_data = config.get('work_wallpaper') if mode_name == get_text('work_mode') else config.get('personal_wallpaper')

    if wallpaper_data and wallpaper_data.get('path'):
        wallpaper_path = wallpaper_data['path']
        if not os.path.exists(wallpaper_path):
            console.log(f"[{STYLE_ERROR}]{get_text('error')}:[/{STYLE_ERROR}] {get_text('wallpaper_not_found', path=wallpaper_path)}")
            time.sleep(2)
        else:
            style_map = {"1": (10, 0), "2": (6, 0), "3": (2, 0), "4": (0, 1), "5": (0, 0), "6": (22, 0)}
            style_key = wallpaper_data.get('style', "1")
            wallpaper_style, tile_wallpaper = style_map.get(style_key, style_map["1"])
            try:
                console.log(f"[dim]{get_text('applying_wallpaper', mode_name=mode_name)}...[/dim]")
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, str(wallpaper_style))
                winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, str(tile_wallpaper))
                winreg.CloseKey(key)
                ctypes.windll.user32.SystemParametersInfoW(20, 0, os.path.abspath(wallpaper_path), 3)
                console.log(f"[bold white]{get_text('wallpaper_applied')}[/bold white]")
            except Exception as e:
                console.log(f"[{STYLE_ERROR}]{get_text('error_applying_wallpaper')}:[/{STYLE_ERROR}] {e}")
    else:
        console.log(f"[dim]{get_text('no_wallpaper_configured', mode_name=mode_name)}[/dim]")

    with console.status(get_text('processing'), spinner="dots") as status:
        manage_processes(apps_to_launch, apps_to_terminate, status)
    
    console.print(f"\n[bold white]{get_text('mode_activated_successfully', mode_name=mode_name)}[/bold white]")
    time.sleep(3)

def view_database():
    show_loading_spinner()
    clear_screen()
    show_header()
    work_apps = load_apps(WORK_DB)
    personal_apps = load_apps(PERSONAL_DB)
    table = Table(title=get_text("view_db_title"), border_style=STYLE_ACCENT, show_lines=True)
    table.add_column(get_text("work_mode_col"), style=STYLE_FG, justify="left")
    table.add_column(get_text("personal_mode_col"), style=STYLE_FG, justify="left")
    max_rows = max(len(work_apps), len(personal_apps))
    for i in range(max_rows):
        work_app_str = ""
        if i < len(work_apps):
            admin_str = f" {get_text('app_info_admin')}" if work_apps[i].get('requires_admin') else ""
            work_app_str = f"[bold]{work_apps[i]['name']}[/bold]{admin_str}\n[dim]{work_apps[i]['path']}[/dim]"
        personal_app_str = ""
        if i < len(personal_apps):
            admin_str = f" {get_text('app_info_admin')}" if personal_apps[i].get('requires_admin') else ""
            personal_app_str = f"[bold]{personal_apps[i]['name']}[/bold]{admin_str}\n[dim]{personal_apps[i]['path']}[/dim]"
        table.add_row(work_app_str, personal_app_str)
    console.print(table)
    Prompt.ask(f"\n{get_text('press_enter_to_return')}")

def add_app_screen():
    while True:
        show_loading_spinner()
        clear_screen()
        show_header()
        console.print(Panel(f"[bold]{get_text('add_app_title')}[/bold]", border_style=STYLE_ACCENT))
        
        db_choice = Prompt.ask(get_text("select_db"), choices=[get_text("db_choice_work"), get_text("db_choice_personal")], default=get_text("db_choice_work"))
        db_name = WORK_DB if db_choice.lower() == get_text("db_choice_work") else PERSONAL_DB
        app_name = Prompt.ask(get_text("app_name_prompt"))
        if app_name == "0":
            console.print(f"\n[dim]{get_text('back_to_main_menu')}[/dim]")
            time.sleep(1)
            break

        console.print(get_text("opening_file_browser"), style="dim")
        app_path = ""
        try:
            root = tk.Tk()
            root.withdraw()
            app_filetypes = [(get_text("file_dialog_executables"), "*.exe"), (get_text("file_dialog_vbscript"), "*.vbs"), (get_text("file_dialog_all_files"), "*.*")]
            app_path = filedialog.askopenfilename(filetypes=app_filetypes)
            root.destroy()
            if not app_path:
                console.print(f"\n[{STYLE_ERROR}]{get_text('no_file_selected')}[/{STYLE_ERROR}]")
                time.sleep(2)
                continue
            console.print(f"{get_text('file_selected')}:{app_path}")
        except Exception as e:
            console.log(f"[{STYLE_ERROR}]{get_text('error')}:[/{STYLE_ERROR}] {get_text('error_opening_file_browser', e=e)}")
            time.sleep(2)
            if not Confirm.ask(get_text('try_again_prompt')): break
            continue
        
        if app_name and app_path:
            close_after_launch = Confirm.ask(get_text("close_after_launch_prompt"))
            requires_admin = Confirm.ask(get_text("requires_admin_prompt"))
            apps = load_apps(db_name)
            apps.append({"name": app_name.upper(), "path": app_path, "close_after_launch": close_after_launch, "requires_admin": requires_admin})
            save_apps(db_name, apps)
            console.print(f"\n[bold white]{get_text('success')}![/bold white] {get_text('app_added_success', name=app_name)}.")
        else:
            console.print(f"\n[{STYLE_ERROR}]{get_text('error')}:[/{STYLE_ERROR}] {get_text('name_path_empty_error')}")
        time.sleep(2)

        if not Confirm.ask(get_text("add_another_app_prompt")): break

def delete_app_screen():
    while True:
        show_loading_spinner(get_text("consulting_records"))
        clear_screen()
        show_header()
        console.print(Panel(f"[bold]{get_text('delete_app_title')}[/bold]", border_style=STYLE_ACCENT))
        db_choice_map = {get_text("db_choice_work"): WORK_DB, get_text("db_choice_personal"): PERSONAL_DB}
        db_choice = Prompt.ask(get_text("select_db"), choices=list(db_choice_map.keys()), default=get_text("db_choice_work"))
        db_name = db_choice_map[db_choice]
        apps = load_apps(db_name)
        if not apps:
            console.print(f"\n{get_text('db_is_empty', db=db_choice.upper())}")
            time.sleep(2)
            break
        
        console.print(f"\n[bold]{get_text('apps_in_db')}[/bold]")
        for i, app in enumerate(apps):
            admin_str = f" {get_text('app_info_admin')}" if app.get('requires_admin') else ""
            console.print(f"  [{i+1}] {app['name']}{admin_str}")
        
        app_index = -1
        while True:
            try:
                choice = Prompt.ask(get_text("delete_app_prompt"))
                if choice == "0": break
                app_index = int(choice) - 1
                if 0 <= app_index < len(apps):
                    break
                else:
                    console.print(f"[{STYLE_ERROR}]{get_text('invalid_number_prompt', max=len(apps))}[/{STYLE_ERROR}]")
            except ValueError:
                console.print(f"[{STYLE_ERROR}]{get_text('invalid_input_prompt')}[/{STYLE_ERROR}]")
        
        if choice == "0":
            console.print(f"\n[dim]{get_text('back_to_main_menu')}[/dim]")
            time.sleep(1)
            break

        app_to_delete = apps[app_index]['name']
        if Confirm.ask(get_text("delete_confirm_prompt", name=app_to_delete)):
            apps.pop(app_index)
            save_apps(db_name, apps)
            console.print(f"\n[bold white]{get_text('success')}![/bold white] {get_text('app_deleted_success', name=app_to_delete)}")
        else:
            console.print(f"\n{get_text('operation_cancelled')}")
        time.sleep(2)

        if not Confirm.ask(get_text("delete_another_app_prompt")): break

def add_wallpaper_screen():
    while True:
        show_loading_spinner(get_text("wallpaper_config_loading"))
        clear_screen()
        show_header()
        console.print(Panel(f"[bold]{get_text('wallpaper_config_title')}[/bold]", border_style=STYLE_ACCENT))
        
        mode_choice_map = {get_text("db_choice_work"): "work_wallpaper", get_text("db_choice_personal"): "personal_wallpaper"}
        mode_name_map = {get_text("db_choice_work"): get_text("work_mode"), get_text("db_choice_personal"): get_text("personal_mode")}
        mode_choice = Prompt.ask(get_text("select_mode_for_wallpaper"), choices=list(mode_choice_map.keys()), default=get_text("db_choice_work"))
        
        console.print(get_text("opening_file_browser_for_mode", mode_name=mode_name_map[mode_choice]), style="dim")
        try:
            root = tk.Tk()
            root.withdraw()
            wallpaper_path = filedialog.askopenfilename(filetypes=[(get_text("image_files"), "*.png *.jpg *.jpeg"), (get_text("file_dialog_all_files"), "*.*")])
            root.destroy()
            if not wallpaper_path:
                console.print(f"\n[{STYLE_ERROR}]{get_text('no_file_selected')}[/{STYLE_ERROR}]\n[dim]{get_text('back_to_main_menu')}[/dim]")
                time.sleep(2)
                break
            console.print(f"{get_text('file_selected')}:{wallpaper_path}")
        except Exception as e:
            console.log(f"[{STYLE_ERROR}]{get_text('error')}:[/{STYLE_ERROR}] {get_text('error_opening_file_browser', e=e)}")
            time.sleep(2)
            if not Confirm.ask(get_text('try_again_prompt')): break
            continue

        style_choices = {"1": get_text("style_fill"), "2": get_text("style_fit"), "3": get_text("style_stretch"), "4": get_text("style_tile"), "5": get_text("style_center"), "6": get_text("style_span")}
        console.print(f"\n[bold]{get_text('select_wallpaper_style')}[/bold]")
        for key, value in style_choices.items(): console.print(f"  [{key}] {value}")
        
        selected_style_key = Prompt.ask(get_text("choose_option"), choices=list(style_choices.keys()), default="1")
        
        current_config = config.copy()
        current_config[mode_choice_map[mode_choice]] = {"path": wallpaper_path, "style": selected_style_key}
        save_config(current_config)
        
        console.print(f"\n[bold white]{get_text('success')}![/bold white] {get_text('wallpaper_set_success', mode_name=mode_name_map[mode_choice], style_name=style_choices[selected_style_key])}")
        time.sleep(2)

        if not Confirm.ask(get_text("configure_another_wallpaper_prompt")): break

def restore_to_default():
    show_loading_spinner(get_text("restore_loading"))
    clear_screen()
    show_header()
    console.print(Panel(f"[bold]{get_text('restore_title')}[/bold]", border_style=STYLE_ACCENT))
    
    if Confirm.ask(get_text("restore_warning")):
        try:
            for db_file in [WORK_DB, PERSONAL_DB, CONFIG_DB]:
                db_path = get_db_path(db_file)
                if os.path.exists(db_path):
                    os.remove(db_path)
                    console.log(f"[dim]{get_text('removed')}:[/dim] {db_file}")
            
            console.print(f"\n[bold white]{get_text('system_restored')}[/bold white]")
            console.print(f"[dim]{get_text('restart_app_prompt')}[/dim]")
            time.sleep(4)
            sys.exit()
        except Exception as e:
            console.print(f"[{STYLE_ERROR}]{get_text('error_restoring')}:[/{STYLE_ERROR}] {e}")
            time.sleep(3)
    else:
        console.print(f"\n[dim]{get_text('operation_cancelled')}[/dim]")
        time.sleep(2)

def main():
    global LANG, config
    os.system("title LUMON OS")
    
    config = load_config()
    user_name = config.get("user_name")

    if not user_name:
        # FIRST RUN EXPERIENCE
        clear_screen()
        console.print(Align.center(Panel(Text("CHOOSE YOUR LANGUAGE / ESCOLHA SEU IDIOMA", justify="center", style="bold white"), border_style="white")))
        console.print("\n")
        console.print(Align.center("1. ENGLISH"))
        console.print(Align.center("2. PORTUGUÊS (BRASILEIRO)"))
        
        while True:
            lang_choice = Prompt.ask(f"\n[{STYLE_ACCENT}]>>>[/{STYLE_ACCENT}] ", show_choices=False, show_default=False)
            if lang_choice == '1':
                LANG = 'en'
                break
            elif lang_choice == '2':
                LANG = 'pt'
                break
            else:
                console.print(f"\n[{STYLE_ERROR}]INVALID OPTION / OPÇÃO INVÁLIDA.[/]\n")
        
        config['language'] = LANG
        
        show_splash_screen()
        clear_screen()
        console.print(Align.center(Panel(Text(get_text("welcome_to_severance"), justify="center", style="bold white"), border_style="white")))
        console.print("\n")
        console.print(Align.center(Text(get_text("what_is_your_name_innie"))))
        user_name = Prompt.ask("")
        config["user_name"] = user_name.strip().title()
        save_config(config)
        
        console.rule(style=STYLE_MATRIX)
        type_text_effect(get_text("verifying_credentials"), style=STYLE_MATRIX)
        console.rule(style=STYLE_MATRIX)
        time.sleep(1)
        clear_screen()
        console.print(Panel(Text(get_text("access_granted"), justify="center", style="bold white"), border_style="white"))
        time.sleep(2)
        clear_screen()
        crypto_animation("SEVERANCE SYSTEM")
        time.sleep(2)
        clear_screen()
        console.print(Align.center(Panel(Text(get_text("hello_prepared_for_new_day", user_name=user_name.strip().title()), justify="center", style="bold white"), border_style="white")))
        time.sleep(3)
    else: 
        # SUBSEQUENT RUNS
        LANG = config.get('language', 'pt')
        show_splash_screen()
        console.print(Align.center(Panel(Text(get_text("welcome_back", user_name=user_name.strip().title()), justify="center", style="bold white"), border_style="white")))
        time.sleep(2)

    # --- MAIN LOOP ---
    while True:
        show_main_menu()
        console.print(f"\n[{STYLE_ACCENT}]>>>[/{STYLE_ACCENT}] ", end="")
        choice = input()

        if choice == "*":
            LANG = 'en' if LANG == 'pt' else 'pt'
            config['language'] = LANG
            save_config(config)
            continue
        elif choice == "1": start_mode(get_text("work_mode"), load_apps(WORK_DB), load_apps(PERSONAL_DB))
        elif choice == "2": start_mode(get_text("personal_mode"), load_apps(PERSONAL_DB), load_apps(WORK_DB))
        elif choice == "3": add_app_screen()
        elif choice == "4": view_database()
        elif choice == "5": delete_app_screen()
        elif choice == "6": add_wallpaper_screen()
        elif choice == "7": clear_system_junk(console)
        elif choice == "8": restore_to_default()
        elif choice == "9": break
        else:
            console.print(f"\n[{STYLE_ERROR}]{get_text('invalid_option')}[/]\n")
            time.sleep(1)

    clear_screen()
    user_name = config.get("user_name", "")
    console.print(Align.center(Panel(Text(get_text("goodbye", user_name=user_name.strip().title()), justify="center", style="bold white"), border_style="white")))
    time.sleep(2)
    console.print(f"\n{get_text('shutting_down')}...", style="bold white")
    time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n\n{get_text('emergency_shutdown')}", style="bold red")
        time.sleep(1)