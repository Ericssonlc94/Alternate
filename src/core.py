"""
Núcleo (engine) do Alternate.

Este módulo concentra a lógica que NÃO depende de interface (Qt, terminal, GUI).
A GUI importa daqui; qualquer outra interface pode fazer o mesmo, sem duplicar código.

Sub-passo 1: camada de dados (paths + leitura/escrita de JSON).
"""

import json
import os
import sys
import time
import uuid
import subprocess
import ctypes
import winreg
import shutil
import psutil  # pyright: ignore[reportMissingModuleSource]
import pygetwindow as gw  # pyright: ignore[reportMissingImports]
import pyautogui  # pyright: ignore[reportMissingModuleSource]

# --- CONSTANTS ---
WORK_DB = "work_apps.json"
PERSONAL_DB = "personal_apps.json"
CONFIG_DB = "config.json"

# Mapeia o estilo escolhido pelo usuário -> (WallpaperStyle, TileWallpaper) do registro.
WALLPAPER_STYLE_MAP = {"1": (10, 0), "2": (6, 0), "3": (2, 0), "4": (0, 1), "5": (0, 0), "6": (22, 0)}


# --- REPORTER (ponte núcleo -> apresentação) ---
class Reporter:
    """Contrato de eventos entre o núcleo e a camada de apresentação.

    O núcleo NÃO conhece Qt, idioma ou GUI. Ele apenas chama estes métodos
    passando uma CHAVE (a mesma do dicionário i18n) e dados. Quem implementa
    (hoje o `QtReporter` da GUI) decide como traduzir e exibir.

    - status: operação em andamento (texto de spinner / barra de status).
    - info:   marco concluído (ex.: "3 processos terminados").
    - detail: evento granular (ex.: "iniciado: Steam"). `subject` = complemento dinâmico.
    - error:  falha não-fatal.

    Esta classe base é no-op: usá-la faz o núcleo rodar em silêncio.
    """

    def status(self, key, **kwargs):
        pass

    def info(self, key, **kwargs):
        pass

    def detail(self, key, subject=None, **kwargs):
        pass

    def error(self, key, subject=None, **kwargs):
        pass


# --- PATHS / LAYOUT ---
# O projeto separa o que o usuário altera (data/, logs/) do que é distribuído
# junto com o programa (assets/). A distinção importa ao empacotar: o PyInstaller
# descompacta os assets numa pasta temporária a cada execução, enquanto os dados
# precisam sobreviver ao lado do executável.
DATA_DIR = "data"
ASSETS_DIR = "assets"
LOGS_DIR = "logs"

# Usado só no plano B de gravação (ver `_writable_dir`), para nomear a pasta em
# %APPDATA%. Não é o título da janela — esse vem das traduções.
APP_NAME = "Alternate"


def get_project_root():
    """Raiz do projeto — a pasta que contém data/, assets/, logs/ e src/.

    Rodando do código-fonte este arquivo está em src/, então a raiz é dois níveis
    acima; empacotado, é a pasta do executável. Resolver a partir de `__file__`
    (e não do diretório de trabalho) mantém os caminhos corretos independente de
    onde o programa foi iniciado.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _can_write(path):
    """Cria o diretório e confirma que dá para gravar nele.

    Não basta `os.makedirs`: em Arquivos de Programas a pasta pode até existir e
    ainda assim recusar escrita para um usuário comum. Só um arquivo de teste
    responde de verdade.
    """
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".write_test")
        with open(probe, "w"):
            pass
        os.remove(probe)
        return True
    except OSError:
        return False


def _writable_dir(name):
    """Devolve a pasta gravável para `name` (data/, logs/).

    Preferência é ao lado do programa — é o modo portátil, e o que vale rodando
    do código-fonte. Instalado numa pasta protegida, gravar ali falharia; nesse
    caso cai para %APPDATA%\\Alternate\\<name>, que é sempre do usuário.
    """
    beside = os.path.join(get_project_root(), name)
    if _can_write(beside):
        return beside
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    fallback = os.path.join(base, APP_NAME, name)
    os.makedirs(fallback, exist_ok=True)
    return fallback


def get_data_dir():
    """Pasta dos dados graváveis (config e bancos de apps); criada se faltar."""
    return _writable_dir(DATA_DIR)


def get_logs_dir():
    """Pasta de logs; criada se faltar."""
    return _writable_dir(LOGS_DIR)


def get_asset_path(*parts):
    """Caminho de um recurso somente-leitura (o logo, as traduções).

    `sys._MEIPASS` é a pasta temporária onde o PyInstaller descompacta o que foi
    declarado em `datas`. Fora do executável esse atributo não existe e assets/
    fica na raiz do projeto.
    """
    base = getattr(sys, "_MEIPASS", None) or get_project_root()
    return os.path.join(base, ASSETS_DIR, *parts)


# --- DATABASE / PERSISTENCE ---
def get_db_path(db_name):
    return os.path.join(get_data_dir(), db_name)


def load_apps(db_name):
    """Carrega a lista de apps de um banco. Retorna [] se não existir/estiver corrompido."""
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


LANG_DIR = "lang"


def load_translations():
    """Carrega todos os idiomas de assets/lang/*.json -> {codigo: {chave: texto}}.

    Cada arquivo (ex.: assets/lang/pt.json, assets/lang/en.json) vira uma entrada cujo código é
    o nome do arquivo sem extensão. Arquivos ausentes/corrompidos são ignorados.
    """
    result = {}
    lang_dir = get_asset_path(LANG_DIR)
    if os.path.isdir(lang_dir):
        for filename in sorted(os.listdir(lang_dir)):
            if filename.lower().endswith(".json"):
                code = os.path.splitext(filename)[0]
                try:
                    with open(os.path.join(lang_dir, filename), "r", encoding="utf-8") as f:
                        result[code] = json.load(f)
                except (OSError, json.JSONDecodeError):
                    continue
    return result


def load_config():
    """Carrega config.json. Retorna {} no primeiro uso (arquivo ausente/corrompido)."""
    config_path = get_db_path(CONFIG_DB)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(config):
    """Grava config.json. Diferente da versão antiga da CLI, NÃO mexe em estado global."""
    config_path = get_db_path(CONFIG_DB)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


# --- SYSTEM INFO ---
def get_battery():
    """Estado da bateria como (percentual, na_tomada), ou None em desktops.

    Fica no núcleo — e não na interface — porque é leitura de hardware; a CLI e a
    GUI apenas formatam o resultado.
    """
    try:
        battery = psutil.sensors_battery()
    except Exception:
        return None
    if battery is None:
        return None
    return int(battery.percent), bool(battery.power_plugged)


# --- PROCESS MANAGEMENT ---
def manage_processes(apps_to_launch, apps_to_terminate, reporter=None):
    """Encerra os apps do modo anterior e inicia os do modo atual.

    `reporter`: instância de Reporter (ou None para rodar em silêncio).
    """
    reporter = reporter or Reporter()

    # 1. IDENTIFICA APPS COMPARTILHADOS (não encerra o que também vai ser iniciado)
    launch_paths = {os.path.normcase(app['path']) for app in apps_to_launch}
    apps_to_terminate = [app for app in apps_to_terminate if os.path.normcase(app['path']) not in launch_paths]

    # 2. TERMINAÇÃO
    reporter.status('terminating_apps')
    terminated_count = 0
    if apps_to_terminate:
        running_procs = list(psutil.process_iter(['pid', 'name', 'exe']))

        for app in apps_to_terminate:
            app_name_lower = app["name"].lower()

            # Terminação agressiva para o Dropbox
            if "dropbox" in app_name_lower:
                for p in running_procs:
                    try:
                        p_name = p.name().lower()
                        p_exe = os.path.basename(p.info['exe']).lower() if p.info['exe'] else ''
                        if "dropbox" in p_name or "dropbox" in p_exe:
                            p.terminate()  # tenta encerrar graciosamente primeiro
                            try:
                                p.wait(timeout=2)
                            except psutil.TimeoutExpired:
                                p.kill()  # força se não encerrar em 2s
                            terminated_count += 1
                            reporter.detail('terminated_aggressively', subject=f"{p.name()} (PID: {p.pid})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            # Terminação padrão para os demais apps
            else:
                for p in running_procs:
                    try:
                        p_exe = os.path.normcase(p.info['exe']) if p.info['exe'] else ''
                        if p_exe == os.path.normcase(app["path"]):
                            p.terminate()
                            terminated_count += 1
                            reporter.detail('terminated', subject=f"{app['name']} (PID: {p.pid})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        reporter.error('failed_to_terminate', subject=app['name'])
                        continue

    reporter.info('processes_terminated', count=terminated_count)
    time.sleep(1)

    # 3. INICIALIZAÇÃO
    reporter.status('starting_apps')
    launched_count = 0
    if apps_to_launch:
        running_app_paths = {os.path.normcase(p.info['exe']) for p in psutil.process_iter(['exe']) if p.info.get('exe')}
        for app in apps_to_launch:
            app_path = app["path"]
            app_name_lower = app["name"].lower()

            if os.path.normcase(app_path) in running_app_paths:
                reporter.detail('already_running', subject=app['name'])
                continue

            try:
                _, ext = os.path.splitext(app_path)
                requires_admin = app.get("requires_admin", False)
                work_dir = os.path.dirname(app_path)

                # Inicia minimizado por padrão (SW_MINIMIZE = 6). Definido uma vez
                # aqui para todos os ramos abaixo reutilizarem.
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 6

                # Tratamento especial: Steam
                if "steam" in app_name_lower:
                    subprocess.Popen([app_path, "-silent"], cwd=work_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    launched_count += 1
                    reporter.detail('started', subject=app['name'])
                # Tratamento especial: Dropbox (delay pós-início + silencia saída)
                elif "dropbox" in app_name_lower:
                    subprocess.Popen([app_path], startupinfo=startupinfo, cwd=work_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    launched_count += 1
                    reporter.detail('started', subject=app['name'])
                    time.sleep(3)
                # Execução como administrador
                elif requires_admin:
                    executable = "wscript.exe" if ext.lower() == ".vbs" else app_path
                    params = f'"{app_path}"' if ext.lower() == ".vbs" else None
                    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, work_dir, 1)
                    if ret > 32:
                        launched_count += 1
                        reporter.detail('started', subject=app['name'])
                    else:
                        raise OSError(f"ShellExecuteW failed with error code {ret}. User may have cancelled the UAC prompt.")

                # Execução padrão (sem admin)
                else:
                    if ext.lower() == ".vbs":
                        subprocess.Popen(["wscript.exe", app_path], cwd=work_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        # Apps Electron (ex.: Dropbox): silencia a saída para reduzir ruído
                        if "dropbox" in app_name_lower or "electron" in app_path.lower():
                            subprocess.Popen([app_path], startupinfo=startupinfo, cwd=work_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            subprocess.Popen([app_path], startupinfo=startupinfo, cwd=work_dir)
                    launched_count += 1
                    reporter.detail('started', subject=app['name'])

                time.sleep(0.2)
            except Exception as e:
                reporter.error('failed_to_start', subject=f"{app['name']} - {e}")

    reporter.info('apps_launched', count=launched_count)
    time.sleep(1)

    # 4. FECHAR INTERFACES DOS APPS MARCADOS COM close_after_launch
    apps_to_close = [app for app in apps_to_launch if app.get("close_after_launch")]
    if apps_to_close:
        reporter.status('finishing_interfaces')
        time.sleep(4)
        for app in apps_to_close:
            try:
                app_name = app.get("name")
                if not app_name:
                    continue
                windows = [w for w in gw.getAllWindows() if app_name.lower() in w.title.lower()]
                if not windows:
                    short_name = app_name.split()[0]
                    windows = [w for w in gw.getAllWindows() if short_name.lower() in w.title.lower()]
                if windows:
                    window = windows[0]
                    reporter.detail('closing_window_alt_f4', title=window.title)
                    window.activate()
                    time.sleep(1)
                    pyautogui.hotkey('alt', 'f4')
                    time.sleep(0.5)
            except Exception as e:
                reporter.error('could_not_close_window', name=app.get('name', 'unknown'), e=e)


# --- WALLPAPER ---
SPI_SETDESKWALLPAPER = 20
SPIF_UPDATE_AND_NOTIFY = 3  # SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE
VD_ROOT = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops"
VD_BASE = VD_ROOT + r"\Desktops"

# Tempo de acomodação após alternar de área de trabalho. O Windows anima a
# transição e ignora a troca de papel de parede enquanto ela acontece.
VD_SWITCH_SETTLE = 0.6


def _set_wallpaper_now(abspath):
    """Aplica o papel de parede na área de trabalho virtual ATIVA.

    Esta é a única chamada que realmente REPINTA a tela — e só a área ativa.
    """
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, abspath, SPIF_UPDATE_AND_NOTIFY)


def apply_wallpaper(wallpaper_data, mode_name, reporter=None):
    """Aplica o papel de parede configurado para o modo (via registro do Windows)."""
    reporter = reporter or Reporter()

    if not (wallpaper_data and wallpaper_data.get('path')):
        reporter.detail('no_wallpaper_configured', mode_name=mode_name)
        return

    wallpaper_path = wallpaper_data['path']
    if not os.path.exists(wallpaper_path):
        reporter.error('wallpaper_not_found', path=wallpaper_path)
        time.sleep(2)
        return

    style_key = wallpaper_data.get('style', "1")
    wallpaper_style, tile_wallpaper = WALLPAPER_STYLE_MAP.get(style_key, WALLPAPER_STYLE_MAP["1"])
    try:
        abspath = os.path.abspath(wallpaper_path)

        # Nada a fazer: evita percorrer as áreas de trabalho à toa (ex.: iniciar o
        # mesmo modo duas vezes seguidas).
        if _wallpaper_already_applied(abspath, wallpaper_style, tile_wallpaper):
            reporter.detail('wallpaper_already_applied', mode_name=mode_name)
            return

        reporter.detail('applying_wallpaper', mode_name=mode_name)

        # Estilo (Fill/Fit/Stretch/Tile/Center/Span). "Span" cobre múltiplos monitores.
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, str(wallpaper_style))
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, str(tile_wallpaper))
        winreg.CloseKey(key)

        # Aplica na área de trabalho ATIVA. O Windows renderiza a imagem em todos
        # os monitores conforme o estilo acima.
        _set_wallpaper_now(abspath)
        reporter.info('wallpaper_applied')

        # Propaga para as DEMAIS áreas de trabalho virtuais (Task View / Win+Tab).
        vd_count = _apply_wallpaper_to_virtual_desktops(abspath, reporter)
        if vd_count > 1:
            reporter.detail('wallpaper_all_desktops', count=vd_count)
    except Exception as e:
        reporter.error('error_applying_wallpaper', subject=str(e))


def _wallpaper_already_applied(abspath, style, tile):
    """Diz se o papel de parede alvo já está em vigor em TODAS as áreas.

    Serve para pular o percurso pelas áreas de trabalho quando não há nada a
    mudar. Compara também o estilo: só o caminho coincidir não basta se o usuário
    trocou de "Ajustar" para "Preencher".

    Na dúvida devolve False — reaplicar é inofensivo, deixar de aplicar não.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop") as k:
            atual = winreg.QueryValueEx(k, "Wallpaper")[0]
            if os.path.normcase(atual) != os.path.normcase(abspath):
                return False
            if winreg.QueryValueEx(k, "WallpaperStyle")[0] != str(style):
                return False
            if winreg.QueryValueEx(k, "TileWallpaper")[0] != str(tile):
                return False
    except OSError:
        return False

    guids = _get_current_virtual_desktop_guids()
    if not guids:
        return False
    for guid in guids:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, VD_BASE + "\\" + guid) as dk:
                if os.path.normcase(winreg.QueryValueEx(dk, "Wallpaper")[0]) != os.path.normcase(abspath):
                    return False
        except OSError:
            return False  # área sem valor: não dá para afirmar que está aplicado
    return True


def _get_current_virtual_desktop_guids():
    """Retorna os GUIDs dos desktops virtuais ATUAIS (na ordem em que aparecem).

    A lista fica no valor binário `VirtualDesktopIDs` (uma sequência de GUIDs de
    16 bytes cada). É importante usar essa lista — e não enumerar a chave `Desktops`
    diretamente — porque o Windows acumula ali dezenas de entradas órfãs de desktops
    já excluídos, que não devem ser tocadas.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, VD_ROOT) as k:
            raw, _ = winreg.QueryValueEx(k, "VirtualDesktopIDs")
    except (FileNotFoundError, OSError):
        return []
    # Cada GUID ocupa 16 bytes no formato mixed-endian do Windows (uuid.bytes_le).
    return ["{" + str(uuid.UUID(bytes_le=raw[i:i + 16])).upper() + "}"
            for i in range(0, len(raw) - 15, 16)]


def _get_current_desktop_index(guids=None):
    """Posição da área de trabalho ativa dentro da lista de GUIDs.

    Necessária para voltar exatamente para onde o usuário estava depois de
    percorrer as áreas. Em qualquer falha assume 0, que é sempre um índice válido.
    """
    guids = _get_current_virtual_desktop_guids() if guids is None else guids
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, VD_ROOT) as k:
            raw, _ = winreg.QueryValueEx(k, "CurrentVirtualDesktop")
        return guids.index("{" + str(uuid.UUID(bytes_le=raw)).upper() + "}")
    except (OSError, ValueError):
        return 0


def _switch_desktop(direction, times):
    """Alterna `times` áreas de trabalho para 'left' ou 'right'.

    Ctrl+Win+Seta é o atalho padrão do Windows. Os saltos são sempre calculados
    para ficar dentro dos limites da lista, nunca dependendo do comportamento de
    dar a volta (que é opcional e varia entre builds do Windows 11).
    """
    for _ in range(times):
        pyautogui.hotkey("ctrl", "winleft", direction)
        time.sleep(VD_SWITCH_SETTLE)


def _apply_wallpaper_to_virtual_desktops(abspath, reporter=None):
    """Aplica o papel de parede em TODAS as áreas de trabalho virtuais.

    Gravar `HKCU\\...\\VirtualDesktops\\Desktops\\{GUID}\\Wallpaper` NÃO basta: o
    Explorer mantém o papel de parede de cada área em memória e só consulta essas
    chaves ao iniciar a sessão. Escrevendo apenas o registro, a imagem troca na
    área ativa (via SystemParametersInfoW) e nas demais só depois de reiniciar o
    Explorer — que foi exatamente o sintoma relatado.

    Por isso aqui fazemos as duas coisas: gravamos o registro (para o valor estar
    certo no próximo login) e percorremos as áreas aplicando de fato em cada uma.

    Retorna em quantas áreas o papel de parede foi aplicado.
    """
    reporter = reporter or Reporter()
    guids = _get_current_virtual_desktop_guids()
    if not guids:
        return 0

    # 1. Registro: mantém o valor correto para a próxima sessão.
    for guid in guids:
        try:
            # CreateKey abre se existir ou cria se faltar (não toca em outros valores).
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, VD_BASE + "\\" + guid) as dk:
                winreg.SetValueEx(dk, "Wallpaper", 0, winreg.REG_SZ, abspath)
        except OSError:
            continue  # uma área falhou: segue para a próxima

    # A área ativa já foi repintada por quem chamou; com uma só, acabou.
    if len(guids) == 1:
        return 1

    # Percorrer as áreas alterna a tela do usuário. Quem não quiser esse efeito
    # desliga em data/config.json e fica só com a área ativa + o registro.
    if not load_config().get("wallpaper_walk_desktops", True):
        return 1

    # 2. Visita cada área e aplica de verdade.
    start = _get_current_desktop_index(guids)
    position = start
    applied = 0
    try:
        _switch_desktop("left", position)  # vai até a primeira
        position = 0
        for index in range(len(guids)):
            if index:
                _switch_desktop("right", 1)
                position = index
            _set_wallpaper_now(abspath)
            applied += 1
    except Exception as e:
        reporter.error('error_applying_wallpaper', subject=str(e))
    finally:
        # Devolve o usuário para a área de onde ele saiu, mesmo se algo falhou.
        if position > start:
            _switch_desktop("left", position - start)
        elif position < start:
            _switch_desktop("right", start - position)
    return applied or 1


VD_BACKUP_DB = "virtual_desktops_backup.json"


def _jsonable(value):
    """Torna um valor de registro serializável em JSON (bytes -> hex marcado)."""
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    return value


def clean_orphan_virtual_desktops(reporter=None):
    """Remove do registro as entradas de wallpaper de desktops virtuais que não
    existem mais (o Windows nunca limpa esses órfãos).

    Segurança: só remove GUIDs AUSENTES da lista de desktops atuais
    (VirtualDesktopIDs); se essa lista não puder ser lida, não remove nada. Antes
    de apagar, grava um backup de todos os valores em `virtual_desktops_backup.json`
    (acumulando o histórico de execuções), para permitir restauração manual.

    Retorna (removidos, caminho_do_backup).
    """
    reporter = reporter or Reporter()
    reporter.info('vd_cleanup_start')

    current = {g.upper() for g in _get_current_virtual_desktop_guids()}
    if not current:
        # Sem lista confiável de desktops atuais: não arrisca apagar nada.
        reporter.detail('vd_cleanup_skipped')
        return 0, None

    # 1. Coleta os GUIDs órfãos e seus valores (para o backup).
    orphans = {}
    try:
        parent = winreg.OpenKey(winreg.HKEY_CURRENT_USER, VD_BASE)
    except FileNotFoundError:
        reporter.info('vd_cleanup_none')
        return 0, None
    try:
        idx = 0
        while True:
            try:
                name = winreg.EnumKey(parent, idx)
            except OSError:
                break  # acabaram os subkeys
            idx += 1
            if name.upper() in current:
                continue  # desktop atual: preservar
            values = {}
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, VD_BASE + "\\" + name) as sub:
                    vi = 0
                    while True:
                        try:
                            vname, vdata, _vtype = winreg.EnumValue(sub, vi)
                        except OSError:
                            break
                        vi += 1
                        values[vname] = _jsonable(vdata)
            except OSError:
                pass
            orphans[name] = values
    finally:
        winreg.CloseKey(parent)

    if not orphans:
        reporter.info('vd_cleanup_none')
        return 0, None

    # 2. Backup (acumula histórico de execuções).
    backup_path = get_db_path(VD_BACKUP_DB)
    try:
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        history.append({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "removed": orphans})
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
        reporter.detail('vd_cleanup_backup', subject=backup_path)
    except OSError:
        backup_path = None  # não conseguiu gravar backup

    # 3. Remove os órfãos (só após o backup estar salvo).
    removed = 0
    for name in orphans:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, VD_BASE + "\\" + name)
            removed += 1
        except OSError:
            continue  # ex.: subkey com filhos ou sem permissão — pula

    reporter.info('vd_cleanup_done', count=removed)
    return removed, backup_path


# --- SYSTEM JUNK ---
def clear_system_junk(reporter=None):
    """Remove arquivos temporários do Windows (%TEMP% e Windows\\Temp)."""
    reporter = reporter or Reporter()

    reporter.info('clearing_cache')
    temp_dirs = [os.environ.get('TEMP'), os.path.join(os.environ.get('WINDIR', 'C:/Windows'), 'Temp')]
    cleaned_count = 0
    for temp_dir in temp_dirs:
        if not temp_dir or not os.path.exists(temp_dir):
            continue
        try:
            for item_name in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item_name)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    cleaned_count += 1
                    reporter.detail('removed', subject=item_path)
                except PermissionError:
                    reporter.error('permission_denied', subject=item_path)
                except OSError as e:
                    reporter.error('error_removing', subject=f"{item_path} - {e}")
        except PermissionError:
            reporter.error('permission_denied_listing', dir=temp_dir)
        except OSError as e:
            reporter.error('error_accessing', subject=f"{temp_dir} - {e}")
    reporter.info('temp_items_removed', count=cleaned_count)
    time.sleep(1)
