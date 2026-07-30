import psutil # pyright: ignore[reportMissingModuleSource]
import time
import sys
import os
import winsound
import random
import string
import tkinter as tk
from tkinter import filedialog
from rich.console import Console # pyright: ignore[reportMissingImports]
from rich.panel import Panel # pyright: ignore[reportMissingImports]
from rich.text import Text # pyright: ignore[reportMissingImports]
from rich.prompt import Prompt, Confirm # pyright: ignore[reportMissingImports]
from rich.table import Table # pyright: ignore[reportMissingImports]
from rich.live import Live # pyright: ignore[reportMissingImports]
from rich.align import Align # pyright: ignore[reportMissingImports]

import core
from core import (
    WORK_DB, PERSONAL_DB, CONFIG_DB,
    get_db_path, load_apps, save_apps, load_config,
)

# --- CONSTANTS ---
STYLE_BG = "on #001E29"
STYLE_FG = "white"
STYLE_ACCENT = "cyan"
STYLE_ERROR = "bold red"
STYLE_MATRIX = "white"

console = Console(style=f"{STYLE_FG} {STYLE_BG}")

# --- I18N (Internationalization) ---
# Traduções carregadas de assets/lang/*.json (ver core.load_translations).
i18n = core.load_translations()

# --- GLOBAL CONFIG & LANG ---
config = {}
LANG = 'pt' # Default language, will be updated on load

def get_text(key, **kwargs):
    """Fetches a text from the i18n dictionary for the current language."""
    table = i18n.get(LANG) or i18n.get('pt') or {}
    return table.get(key, f"<{key}>").format(**kwargs)

# --- DATABASE FUNCTIONS ---
# A camada de dados (get_db_path, load_apps, save_apps, load_config) vive em core.py.
# Aqui fica apenas o wrapper que mantém o estado global `config` desta CLI sincronizado.
def save_config(new_config):
    global config
    config = new_config
    core.save_config(new_config)

# --- PRESENTATION BRIDGE (núcleo -> rich) ---
class RichReporter(core.Reporter):
    """Traduz os eventos do núcleo para a saída rich (cores + i18n desta CLI).

    A GUI, no futuro, terá o seu próprio Reporter (ex.: atualizar labels/log box)
    sem tocar em nada do núcleo.
    """

    def __init__(self, status=None):
        self._status = status  # objeto retornado por console.status(...) ou None

    def status(self, key, **kwargs):
        if self._status is not None:
            self._status.update(f"[bold white]{get_text(key, **kwargs)}[/bold white]")

    def info(self, key, **kwargs):
        console.log(f"[bold white]{get_text(key, **kwargs)}[/bold white]")

    def detail(self, key, subject=None, **kwargs):
        label = get_text(key, **kwargs)
        console.log(f"[dim]{label}:[/dim] {subject}" if subject else f"[dim]{label}[/dim]")

    def error(self, key, subject=None, **kwargs):
        label = get_text(key, **kwargs)
        console.log(f"[{STYLE_ERROR}]{label}:[/{STYLE_ERROR}] {subject}" if subject else f"[{STYLE_ERROR}]{label}[/{STYLE_ERROR}]")


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

def start_mode(mode_name, apps_to_launch, apps_to_terminate):
    show_loading_spinner(get_text('starting_mode', mode_name=mode_name))
    
    current_config = config.copy()
    current_config['active_mode'] = mode_name
    save_config(current_config)

    wallpaper_data = config.get('work_wallpaper') if mode_name == get_text('work_mode') else config.get('personal_wallpaper')

    core.apply_wallpaper(wallpaper_data, mode_name, RichReporter())

    with console.status(get_text('processing'), spinner="dots") as status:
        core.manage_processes(apps_to_launch, apps_to_terminate, RichReporter(status))
    
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
        elif choice == "7":
            reporter = RichReporter()
            core.clear_system_junk(reporter)
            core.clean_orphan_virtual_desktops(reporter)
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