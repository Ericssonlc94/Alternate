import json
import subprocess
import psutil
import time
import sys
import os
import winsound
import random
import string
import pygetwindow as gw
import shutil
import pyautogui
import ctypes
import winreg
import tkinter as tk
from tkinter import filedialog, font
from PIL import Image, ImageTk
import threading

# --- CONSTANTS ---
STYLE_BG = "#001E29"
STYLE_FG = "white"
STYLE_ACCENT = "cyan"
STYLE_ERROR = "red"
STYLE_SUCCESS = "#4AF626"
STYLE_DIM = "gray"
FONT_NAME = "Consolas"
FONT_SIZE = 14
WORK_DB = "work_apps.json"
PERSONAL_DB = "personal_apps.json"
CONFIG_DB = "config.json"

# --- I18N (Internationalization) ---
i18n = {
    'pt': {
        "work_mode": "TRABALHO", "personal_mode": "PESSOAL", "none_mode": "NENHUM", "error": "ERRO", "warning": "AVISO",
        "success": "SUCESSO", "confirm_yes": "s", "confirm_no": "n", "confirm_prompt": "Deseja continuar? (s/n)",
        "try_again_prompt": "Tentar novamente? (s/n)", "back_to_main_menu": "Voltando ao menu principal...",
        "press_enter_to_return": "Pressione [Enter] para voltar ao menu", "created_by": "Created by Ericsson Cardoso",
        "invalid_option": "OPÇÃO INVÁLIDA.", "lumon_industries": "LUMON INDUSTRIES.",
        "connecting_to_mainframe": "CONECTANDO AO MAINFRAME...", "welcome_to_severance": "BEM-VINDO AO SISTEMA SEVERANCE",
        "what_is_your_name_innie": "Qual é o seu nome, innie?", "verifying_credentials": "VERIFICANDO CREDENCIAIS...",
        "access_granted": "ACESSO CONCEDIDO", "hello_prepared_for_new_day": "Olá, {user_name}! Preparado para um novo dia?",
        "welcome_back": "Bem-vindo de volta, {user_name}!", "goodbye": "Até logo, {user_name}! Tenha um bom dia.",
        "shutting_down": "DESLIGANDO SISTEMA...", "emergency_shutdown": "DESLIGAMENTO DE EMERGÊNCIA INICIADO.",
        "main_menu_title": "MENU DE OPÇÕES", "active_mode": "MODO ATIVO", "menu_option_1": "INICIAR MODO DE TRABALHO",
        "menu_option_2": "INICIAR MODO PESSOAL", "menu_option_3": "ADICIONAR APP AO BANCO DE DADOS",
        "menu_option_4": "CONSULTAR BANCO DE DADOS", "menu_option_5": "EXCLUIR APP DO BANCO DE DADOS",
        "menu_option_6": "ADICIONAR PAPEL DE PAREDE", "menu_option_7": "LIMPAR CACHE E ARQUIVOS TEMPORÁRIOS",
        "menu_option_8": "RESTAURAR AO PADRÃO", "menu_option_9": "SAIR", "change_language_prompt": "Mudar Idioma (EN/PT)",
        "battery_charging": "CARREGANDO", "battery_discharging": "DESCARREGANDO", "battery_na": "BATERIA N/A",
        "terminating_apps": "TERMINANDO APLICATIVOS DO MODO ANTERIOR...", "terminated_aggressively": "TERMINADO (KILL AGRESSIVO)",
        "terminated": "TERMINADO", "failed_to_terminate": "FALHA AO TERMINAR", "processes_terminated": "{count} PROCESSOS TERMINADOS.",
        "starting_apps": "INICIANDO APLICATIVOS DO MODO ATUAL...", "already_running": "JÁ EM EXECUÇÃO", "started": "INICIADO",
        "failed_to_start": "FALHA AO INICIAR", "apps_launched": "{count} APLICATIVOS INICIADOS.",
        "finishing_interfaces": "FINALIZANDO INTERFACES...", "closing_window_alt_f4": "Fechando interface de '{title}' com Alt+F4...",
        "could_not_close_window": "Não foi possível fechar a janela de '{name}': {e}", "organizing_desktop": "ORGANIZANDO ÁREA DE TRABALHO...",
        "clearing_cache": "LIMPANDO CACHE E ARQUIVOS TEMPORÁRIOS...", "removed": "Removido", "permission_denied": "PERMISSÃO NEGADA",
        "error_removing": "ERRO AO REMOVER", "permission_denied_listing": "Não foi possível listar o conteúdo de: {dir}. Tente executar como administrador.",
        "error_accessing": "ERRO AO ACESSAR", "temp_items_removed": "{count} ITENS TEMPORÁRIOS REMOVIDOS.",
        "starting_mode": "INICIANDO {mode_name}...", "wallpaper_not_found": "Arquivo de papel de parede não encontrado: {path}",
        "applying_wallpaper": "APLICANDO PAPEL DE PAREDE PARA O MODO {mode_name}...", "wallpaper_applied": "PAPEL DE PAREDE APLICADO.",
        "error_applying_wallpaper": "ERRO AO APLICAR PAPEL DE PAREDE", "no_wallpaper_configured": "Nenhum papel de parede configurado para o modo {mode_name}.",
        "mode_activated_successfully": "MODO {mode_name} ATIVADO COM SUCESSO.", "view_db_title": "BANCO DE DADOS DE APLICATIVOS",
        "work_mode_col": "MODO DE TRABALHO", "personal_mode_col": "MODO PESSOAL", "app_info_admin": "(Requer Admin)",
        "add_app_title": "ADICIONAR NOVO APLICATIVO", "select_db": "Selecione o banco de dados (t=trabalho, p=pessoal):",
        "db_choice_work": "t", "db_choice_personal": "p", "app_name_prompt": "NOME DO APP (ex: Notepad) ou digite [0] para voltar:",
        "opening_file_browser": "Abrindo buscador de arquivos...", "file_selected": "Caminho selecionado",
        "no_file_selected": "Nenhum arquivo selecionado. Operação cancelada.", "error_opening_file_browser": "Não foi possível abrir o buscador de arquivos: {e}",
        "close_after_launch_prompt": "Fechar janela após iniciar? (s/n)", "requires_admin_prompt": "Requer permissão de administrador? (s/n)",
        "app_added_success": "App '{name}' adicionado.", "name_path_empty_error": "Nome e caminho não podem ser vazios.",
        "add_another_app_prompt": "Deseja adicionar outro aplicativo? (s/n)", "file_dialog_executables": "Executáveis",
        "file_dialog_all_files": "Todos os arquivos", "delete_app_title": "EXCLUIR APLICATIVO",
        "consulting_records": "CONSULTANDO REGISTROS...", "db_is_empty": "O banco de dados {db} está vazio.",
        "apps_in_db": "Aplicativos no banco de dados:", "delete_app_prompt": "Digite o NÚMERO do app para excluir ou [0] para voltar:",
        "invalid_number_prompt": "Número inválido.", "invalid_input_prompt": "Entrada inválida. Digite um número.",
        "delete_confirm_prompt": "Tem certeza que deseja excluir '{name}'? (s/n)", "app_deleted_success": "App '{name}' excluído.",
        "operation_cancelled": "Operação cancelada.", "delete_another_app_prompt": "Deseja excluir outro aplicativo? (s/n)",
        "wallpaper_config_title": "CONFIGURAR PAPEL DE PAREDE", "select_mode_for_wallpaper": "Selecione o modo (t=trabalho, p=pessoal):",
        "image_files": "Arquivos de Imagem", "select_wallpaper_style": "Selecione o estilo do papel de parede:",
        "style_fill": "Preencher", "style_fit": "Ajustar", "style_stretch": "Esticar", "style_tile": "Lado a Lado", "style_center": "Centralizar", "style_span": "Span",
        "choose_option": "Escolha uma opção:", "wallpaper_set_success": "Papel de parede para o modo {mode_name} configurado.",
        "configure_another_wallpaper_prompt": "Deseja configurar outro? (s/n)", "restore_title": "RESTAURAR AO PADRÃO",
        "restore_warning": "ATENÇÃO: Esta ação irá apagar TUDO. Tem certeza? (s/n)", "system_restored": "SISTEMA RESTAURADO AO PADRÃO.",
        "restart_app_prompt": "Por favor, reinicie o aplicativo.", "error_restoring": "ERRO AO RESTAURAR",
        "choose_lang": "CHOOSE YOUR LANGUAGE / ESCOLHA SEU IDIOMA", "lang_en": "1. ENGLISH", "lang_pt": "2. PORTUGUÊS (BRASILEIRO)"
    },
    'en': {
        "work_mode": "WORK", "personal_mode": "PERSONAL", "none_mode": "NONE", "error": "ERROR", "warning": "WARNING",
        "success": "SUCCESS", "confirm_yes": "y", "confirm_no": "n", "confirm_prompt": "Do you want to continue? (y/n)",
        "back_to_main_menu": "Returning to main menu...", "press_enter_to_return": "Press [Enter] to return",
        "invalid_option": "INVALID OPTION.", "lumon_industries": "LUMON INDUSTRIES.",
        "main_menu_title": "OPTIONS MENU", "active_mode": "ACTIVE MODE", "menu_option_1": "START WORK MODE",
        "menu_option_2": "START PERSONAL MODE", "menu_option_3": "ADD APP TO DATABASE", "menu_option_4": "VIEW DATABASE",
        "menu_option_5": "DELETE APP FROM DATABASE", "menu_option_6": "SET WALLPAPER", "menu_option_7": "CLEAR CACHE & TEMP FILES",
        "menu_option_8": "RESTORE TO DEFAULT", "menu_option_9": "EXIT", "change_language_prompt": "Change Language (EN/PT)",
        "shutting_down": "SHUTTING DOWN SYSTEM...", "view_db_title": "APPLICATION DATABASE", "work_mode_col": "WORK MODE",
        "personal_mode_col": "PERSONAL MODE", "app_info_admin": "(Requires Admin)",
    }
}

# --- GLOBAL CONFIG & LANG ---
config = {}
LANG = 'pt'

def get_text(key, **kwargs):
    return i18n.get(LANG, i18n['pt']).get(key, f"<{key}>").format(**kwargs)

# --- DATABASE FUNCTIONS ---
def get_db_path(db_name):
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, db_name)

def load_json(db_name, default=[]):
    db_path = get_db_path(db_name)
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(db_name, data):
    db_path = get_db_path(db_name)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_config():
    global config, LANG
    config = load_json(CONFIG_DB, default={})
    LANG = config.get('language', 'pt')

def save_config():
    save_json(CONFIG_DB, config)

# --- MAIN APPLICATION CLASS ---
class TerminalApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LUMON OS")
        self.configure(bg=STYLE_BG)
        self.geometry("1024x768")
        self.current_state = "starting"
        self.state_data = {}

        self.terminal_font = font.Font(family=FONT_NAME, size=FONT_SIZE)
        self.text_area = tk.Text(self, bg=STYLE_BG, fg=STYLE_FG, font=self.terminal_font, insertbackground=STYLE_FG, borderwidth=0, highlightthickness=0, wrap="word")
        self.text_area.pack(expand=True, fill='both', padx=20, pady=10)
        self.text_area.config(state=tk.DISABLED)
        self.setup_tags()

        self.input_frame = tk.Frame(self, bg=STYLE_BG)
        self.input_frame.pack(fill='x', padx=20, pady=(0, 10))
        self.prompt_label = tk.Label(self.input_frame, text=">>>", bg=STYLE_BG, fg=STYLE_ACCENT, font=self.terminal_font)
        self.prompt_label.pack(side=tk.LEFT)
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(self.input_frame, textvariable=self.input_var, bg=STYLE_BG, fg=STYLE_FG, font=self.terminal_font, insertbackground=STYLE_FG, borderwidth=0, highlightthickness=0)
        self.input_entry.pack(fill='x', expand=True, side=tk.LEFT)
        self.input_entry.bind("<Return>", self.process_input)
        self.input_entry.focus_set()

        self.crt_canvas = tk.Canvas(self, bg="black", borderwidth=0, highlightthickness=0, cursor="none")
        self.crt_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.text_area.lift()
        self.input_frame.lift()
        self.after(100, self.draw_scanlines)

        self.run_in_thread(self.startup_sequence)

    # --- UI & Threading Helpers ---
    def setup_tags(self):
        self.text_area.tag_configure("error", foreground=STYLE_ERROR)
        self.text_area.tag_configure("success", foreground=STYLE_SUCCESS)
        self.text_area.tag_configure("accent", foreground=STYLE_ACCENT)
        self.text_area.tag_configure("dim", foreground=STYLE_DIM)
        self.text_area.tag_configure("bold", font=font.Font(family=FONT_NAME, size=FONT_SIZE, weight="bold"))

    def draw_scanlines(self):
        self.crt_canvas.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        for y in range(0, height, 3):
            self.crt_canvas.create_line(0, y, width, y, fill="#000F18", width=1)

    def write_text(self, text, tags=None, new_line=True):
        self.text_area.config(state=tk.NORMAL)
        full_text = text + ('\n' if new_line else '')
        if tags:
            self.text_area.insert(tk.END, full_text, tags)
        else:
            self.text_area.insert(tk.END, full_text)
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)
        self.update_idletasks()

    def type_text_effect(self, text, tags=None, delay=0.025):
        for char in text:
            self.write_text(char, tags=tags, new_line=False)
            try: winsound.Beep(1400, 20)
            except Exception: pass
            time.sleep(delay)
        self.write_text("") # Final newline

    def clear_screen(self):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.config(state=tk.DISABLED)

    def process_input(self, event=None):
        command = self.input_var.get().strip()
        self.input_var.set("")
        if self.current_state != "starting":
            self.write_text(f">>> {command}")
        if command or self.current_state in ["wait_for_enter", "restore_confirm"]:
            self.handle_command(command)

    def run_in_thread(self, target_func, *args, **kwargs):
        thread = threading.Thread(target=target_func, args=args, kwargs=kwargs, daemon=True)
        thread.start()

    def schedule_task(self, delay, task, *args):
        self.after(delay, task, *args)

    # --- State Machine & Command Handling ---
    def handle_command(self, command):
        if command.lower() == 'clear':
            self.show_main_menu()
            return
        if command.lower() == 'exit':
            self.do_exit()
            return

        state_handler = getattr(self, f"handle_state_{self.current_state}", self.handle_state_unknown)
        state_handler(command)

    def handle_state_unknown(self, command):
        self.write_text(f"Unknown state: {self.current_state}", "error")
        self.schedule_task(1000, self.show_main_menu)

    def handle_state_main_menu(self, command):
        if command == "1": self.run_in_thread(self.do_start_mode, "work")
        elif command == "2": self.run_in_thread(self.do_start_mode, "personal")
        elif command == "3": self.do_add_app()
        elif command == "4": self.do_view_database()
        elif command == "5": self.do_delete_app()
        elif command == "6": self.do_add_wallpaper()
        elif command == "7": self.run_in_thread(self.do_clear_junk)
        elif command == "8": self.do_restore_default()
        elif command == "9": self.do_exit()
        elif command == "*": self.do_change_language()
        else:
            self.write_text(get_text('invalid_option'), "error")
            self.schedule_task(500, self.show_main_menu)

    # --- Core Logic Methods (Converted from Console App) ---

    def do_start_mode(self, mode):
        self.clear_screen()
        mode_name = get_text('work_mode') if mode == 'work' else get_text('personal_mode')
        self.write_text(get_text('starting_mode', mode_name=mode_name), 'accent')
        
        # Apply wallpaper
        wallpaper_data = config.get(f'{mode}_wallpaper', {})
        wallpaper_path = wallpaper_data.get('path')
        if wallpaper_path and os.path.exists(wallpaper_path):
            self.write_text(get_text('applying_wallpaper', mode_name=mode_name))
            try:
                style_map = {"1": (10, 0), "2": (6, 0), "3": (2, 0), "4": (0, 1), "5": (0, 0), "6": (22, 0)}
                style_key = wallpaper_data.get('style', "1")
                wallpaper_style, tile_wallpaper = style_map.get(style_key, style_map["1"])
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, str(wallpaper_style))
                winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, str(tile_wallpaper))
                winreg.CloseKey(key)
                ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 3)
                self.write_text(get_text('wallpaper_applied'), 'success')
            except Exception as e:
                self.write_text(f"{get_text('error_applying_wallpaper')}: {e}", 'error')
        else:
            self.write_text(get_text('no_wallpaper_configured', mode_name=mode_name), 'dim')

        # Launch apps
        db_to_load = WORK_DB if mode == 'work' else PERSONAL_DB
        apps = load_json(db_to_load)
        self.write_text(get_text('starting_apps'))
        count = 0
        for app in apps:
            try:
                subprocess.Popen(app['path'])
                self.write_text(f"  - {get_text('started')}: {app['name']}")
                count += 1
            except Exception as e:
                self.write_text(f"  - {get_text('failed_to_start')} {app['name']}: {e}", 'error')
        
        config['active_mode'] = mode_name
        save_config()
        
        self.write_text(f"\n{get_text('mode_activated_successfully', mode_name=mode_name)}", 'success')
        self.schedule_task(2000, self.show_main_menu)

    def do_add_app(self):
        self.clear_screen()
        self.write_text(get_text('add_app_title'), 'bold')
        self.write_text(get_text('select_db'))
        self.state_data = {}
        self.current_state = 'add_app_db'

    def handle_state_add_app_db(self, command):
        choice = command.lower()
        if choice == get_text('db_choice_work'):
            self.state_data['db'] = WORK_DB
        elif choice == get_text('db_choice_personal'):
            self.state_data['db'] = PERSONAL_DB
        else:
            self.write_text(get_text('invalid_option'), 'error')
            self.schedule_task(1000, self.show_main_menu)
            return
        self.write_text(get_text('app_name_prompt'))
        self.current_state = 'add_app_name'

    def handle_state_add_app_name(self, command):
        if command == '0':
            self.show_main_menu()
            return
        self.state_data['name'] = command
        self.write_text(get_text('opening_file_browser'))
        self.schedule_task(100, self.open_file_dialog_for_app)

    def open_file_dialog_for_app(self):
        path = filedialog.askopenfilename(
            title=get_text('file_selected'),
            filetypes=[(get_text('file_dialog_executables'), '*.exe'), (get_text('file_dialog_all_files'), '*.*')]
        )
        if path:
            self.state_data['path'] = path
            self.write_text(f"{get_text('file_selected')}: {path}")
            self.write_text(get_text('close_after_launch_prompt'))
            self.current_state = 'add_app_close'
        else:
            self.write_text(get_text('no_file_selected'), 'error')
            self.schedule_task(1000, self.show_main_menu)

    def handle_state_add_app_close(self, command):
        self.state_data['close'] = command.lower() == get_text('confirm_yes')
        self.write_text(get_text('requires_admin_prompt'))
        self.current_state = 'add_app_admin'

    def handle_state_add_app_admin(self, command):
        self.state_data['admin'] = command.lower() == get_text('confirm_yes')
        app_data = {
            "name": self.state_data['name'],
            "path": self.state_data['path'],
            "close_after_launch": self.state_data['close'],
            "requires_admin": self.state_data['admin']
        }
        db = load_json(self.state_data['db'])
        db.append(app_data)
        save_json(self.state_data['db'], db)
        self.write_text(get_text('app_added_success', name=app_data['name']), 'success')
        self.state_data = {}
        self.schedule_task(1500, self.show_main_menu)

    def do_view_database(self):
        self.clear_screen()
        self.write_text(f"--- {get_text('view_db_title')} ---", 'bold')
        work_apps = load_json(WORK_DB)
        personal_apps = load_json(PERSONAL_DB)
        self.write_text(f"\n--- {get_text('work_mode_col')} ---", 'accent')
        if not work_apps:
            self.write_text(get_text('db_is_empty', db=WORK_DB))
        else:
            for i, app in enumerate(work_apps, 1):
                admin_tag = get_text('app_info_admin') if app.get('admin') else ""
                self.write_text(f"{i}. {app['name']} {admin_tag}")
        self.write_text(f"\n--- {get_text('personal_mode_col')} ---", 'accent')
        if not personal_apps:
            self.write_text(get_text('db_is_empty', db=PERSONAL_DB))
        else:
            for i, app in enumerate(personal_apps, 1):
                admin_tag = get_text('app_info_admin') if app.get('admin') else ""
                self.write_text(f"{i}. {app['name']} {admin_tag}")
        self.write_text("\n")
        self.write_text(get_text('press_enter_to_return'), 'dim')
        self.current_state = "wait_for_enter"

    def do_delete_app(self):
        self.clear_screen()
        self.write_text(get_text('delete_app_title'), 'bold')
        self.write_text(get_text('select_db'))
        self.state_data = {}
        self.current_state = 'delete_app_db'

    def handle_state_delete_app_db(self, command):
        choice = command.lower()
        if choice == get_text('db_choice_work'):
            self.state_data['db'] = WORK_DB
        elif choice == get_text('db_choice_personal'):
            self.state_data['db'] = PERSONAL_DB
        else:
            self.write_text(get_text('invalid_option'), 'error')
            self.schedule_task(1000, self.show_main_menu)
            return
        apps = load_json(self.state_data['db'])
        self.state_data['apps'] = apps
        if not apps:
            self.write_text(get_text('db_is_empty', db=self.state_data['db']), 'error')
            self.schedule_task(1500, self.show_main_menu)
            return
        self.write_text(get_text('apps_in_db'), 'accent')
        for i, app in enumerate(apps, 1):
            self.write_text(f"{i}. {app['name']}")
        self.write_text(get_text('delete_app_prompt'))
        self.current_state = 'delete_app_select'

    def handle_state_delete_app_select(self, command):
        if command == '0':
            self.show_main_menu()
            return
        try:
            index = int(command) - 1
            if 0 <= index < len(self.state_data['apps']):
                app_to_delete = self.state_data['apps'][index]
                self.write_text(get_text('delete_confirm_prompt', name=app_to_delete['name']))
                self.state_data['index_to_delete'] = index
                self.current_state = 'delete_app_confirm'
            else:
                self.write_text(get_text('invalid_number_prompt'), 'error')
                self.schedule_task(1500, self.show_main_menu)
        except ValueError:
            self.write_text(get_text('invalid_input_prompt'), 'error')
            self.schedule_task(1500, self.show_main_menu)

    def handle_state_delete_app_confirm(self, command):
        if command.lower() == get_text('confirm_yes'):
            index = self.state_data['index_to_delete']
            app_to_delete = self.state_data['apps'][index]
            self.state_data['apps'].pop(index)
            save_json(self.state_data['db'], self.state_data['apps'])
            self.write_text(get_text('app_deleted_success', name=app_to_delete['name']), 'success')
        else:
            self.write_text(get_text('operation_cancelled'), 'dim')
        self.schedule_task(1500, self.show_main_menu)

    def do_add_wallpaper(self):
        self.clear_screen()
        self.write_text(get_text('wallpaper_config_title'), 'bold')
        self.write_text(get_text('select_mode_for_wallpaper'))
        self.state_data = {}
        self.current_state = 'add_wallpaper_db'

    def handle_state_add_wallpaper_db(self, command):
        choice = command.lower()
        if choice == get_text('db_choice_work'):
            self.state_data['mode'] = 'work'
        elif choice == get_text('db_choice_personal'):
            self.state_data['mode'] = 'personal'
        else:
            self.write_text(get_text('invalid_option'), 'error')
            self.schedule_task(1000, self.show_main_menu)
            return
        self.write_text(get_text('select_wallpaper_style'))
        styles = [get_text("style_fill"), get_text("style_fit"), get_text("style_stretch"), get_text("style_tile"), get_text("style_center"), get_text("style_span")]
        for i, style in enumerate(styles, 1):
            self.write_text(f"[{i}] {style}")
        self.current_state = 'add_wallpaper_style'

    def handle_state_add_wallpaper_style(self, command):
        if command in [str(i) for i in range(1, 7)]:
            self.state_data['style'] = command
            self.schedule_task(100, self.open_file_dialog_for_wallpaper)
        else:
            self.write_text(get_text('invalid_option'), 'error')
            self.schedule_task(1000, self.show_main_menu)

    def open_file_dialog_for_wallpaper(self):
        path = filedialog.askopenfilename(
            title=get_text('select_wallpaper_style'),
            filetypes=[(get_text('image_files'), '*.jpg *.jpeg *.png *.bmp'), (get_text('file_dialog_all_files'), '*.*')]
        )
        if path:
            mode = self.state_data['mode']
            style = self.state_data['style']
            config[f'{mode}_wallpaper'] = {"path": path, "style": style}
            save_config()
            self.write_text(get_text('wallpaper_set_success', mode_name=get_text(f'{mode}_mode')), 'success')
        else:
            self.write_text(get_text('no_file_selected'), 'error')
        self.schedule_task(1500, self.show_main_menu)

    def do_clear_junk(self):
        self.clear_screen()
        self.write_text(get_text('clearing_cache'), 'accent')
        dirs_to_clean = [os.environ.get("TEMP"), os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"), "C:\\Windows\\Temp"]
        total_removed = 0
        for d in dirs_to_clean:
            if not d or not os.path.exists(d):
                continue
            self.write_text(f"\n[+] {d}", 'bold')
            try:
                for item in os.listdir(d):
                    full_path = os.path.join(d, item)
                    try:
                        if os.path.isfile(full_path) or os.path.islink(full_path):
                            os.unlink(full_path)
                            total_removed += 1
                        elif os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                            total_removed += 1
                    except (PermissionError, OSError):
                        pass
            except Exception:
                pass
        self.write_text(f"\n{get_text('temp_items_removed', count=total_removed)}", 'success')
        self.write_text("\n")
        self.write_text(get_text('press_enter_to_return'), 'dim')
        self.current_state = "wait_for_enter"

    def do_restore_default(self):
        self.clear_screen()
        self.write_text(get_text('restore_title'), 'error')
        self.write_text(get_text('restore_warning'), 'bold')
        self.current_state = 'restore_confirm'

    def handle_state_restore_confirm(self, command):
        if command.lower() == get_text('confirm_yes'):
            try:
                for db_file in [WORK_DB, PERSONAL_DB, CONFIG_DB]:
                    path = get_db_path(db_file)
                    if os.path.exists(path):
                        os.remove(path)
                self.write_text(get_text('system_restored'), 'success')
                self.write_text(get_text('restart_app_prompt'), 'bold')
                self.schedule_task(2000, self.destroy)
            except Exception as e:
                self.write_text(f"{get_text('error_restoring')}: {e}", 'error')
                self.schedule_task(2000, self.show_main_menu)
        else:
            self.write_text(get_text('operation_cancelled'), 'dim')
            self.schedule_task(1000, self.show_main_menu)

    def do_exit(self):
        self.type_text_effect(get_text("shutting_down"))
        self.schedule_task(1000, self.destroy)

    def do_change_language(self):
        self.clear_screen()
        self.write_text(get_text("choose_lang"), "bold")
        self.write_text(get_text("lang_en"))
        self.write_text(get_text("lang_pt"))
        self.current_state = "change_lang"

    def handle_state_change_lang(self, command):
        global LANG
        if command == '1':
            LANG = 'en'
        elif command == '2':
            LANG = 'pt'
        else:
            self.write_text(get_text('invalid_option'), 'error')
            self.schedule_task(1000, self.show_main_menu)
            return
        config['language'] = LANG
        save_config()
        self.show_main_menu()

    def handle_state_wait_for_enter(self, command):
        self.show_main_menu()

    # --- Startup Sequence ---
    def startup_sequence(self):
        load_config()
        if not config.get("user_name"):
            self.first_run_sequence()
        else:
            self.type_text_effect(get_text("lumon_industries"), "bold")
            self.type_text_effect(get_text("connecting_to_mainframe"))
            time.sleep(1)
            self.clear_screen()
            self.write_text(get_text("welcome_back", user_name=config.get("user_name")), "success")
            self.schedule_task(2000, self.show_main_menu)

    def first_run_sequence(self):
        self.clear_screen()
        self.write_text(get_text("choose_lang"), "bold")
        self.write_text(get_text("lang_en"))
        self.write_text(get_text("lang_pt"))
        self.current_state = "first_run_lang"

    def handle_state_first_run_lang(self, command):
        global LANG
        if command == '1': LANG = 'en'
        elif command == '2': LANG = 'pt'
        else:
            self.write_text(get_text('invalid_option'), 'error')
            return
        config['language'] = LANG
        self.clear_screen()
        self.write_text(get_text("what_is_your_name_innie"))
        self.current_state = "first_run_name"

    def handle_state_first_run_name(self, command):
        user_name = command.strip().title()
        if not user_name: return
        config["user_name"] = user_name
        save_config()
        self.type_text_effect(get_text("verifying_credentials"), "dim")
        time.sleep(1)
        self.clear_screen()
        self.write_text(get_text("access_granted"), "success")
        self.schedule_task(2000, self.show_main_menu)

    def get_battery_status(self):
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return get_text('battery_na')
            percent = int(battery.percent)
            charging = battery.power_plugged
            status = get_text('battery_charging') if charging else get_text('battery_discharging')
            return f"BAT: {percent}% [{status}]"
        except Exception:
            return get_text('battery_na')

    def show_main_menu(self):
        self.clear_screen()
        self.current_state = "main_menu"
        self.prompt_label.config(text=">>>")
        battery = self.get_battery_status()
        self.write_text(f"SYS_OK {' ' * (80 - len(battery) - 6)} {battery}", "accent")
        self.write_text("="*80, "accent")
        self.write_text("SEVERANCE SYSTEM".center(80), "bold")
        self.write_text("="*80, "accent")
        active_mode = config.get('active_mode', get_text('none_mode'))
        self.write_text(f"{get_text('active_mode')}: {active_mode}".center(80), "dim")
        self.write_text("")
        self.write_text(f"--- {get_text('main_menu_title')} ---", "bold")
        menu_options = [
            ("1", get_text("menu_option_1")),
            ("2", get_text("menu_option_2")),
            ("3", get_text("menu_option_3")),
            ("4", get_text("menu_option_4")),
            ("5", get_text("menu_option_5")),
            ("6", get_text("menu_option_6")),
            ("7", get_text("menu_option_7")),
            ("8", get_text("menu_option_8")),
            ("9", get_text("menu_option_9"))
        ]
        for num, desc in menu_options:
            self.write_text(f"[{num}]........... {desc}")
        self.write_text("---" * 20, "dim")
        self.write_text(f"{get_text('created_by')} {' ' * 20} [*] {get_text('change_language_prompt')}", "dim")
        self.write_text("")

if __name__ == "__main__":
    app = TerminalApp()
    app.mainloop()
