"""Janela principal do Severance System.

Organização: um `QStackedWidget` alterna entre três páginas — a abertura
(ROBCO-LUMON), a tela de bloqueio (tema Fallout) e a interface real. A interface
real são duas abas — controle e banco de dados —, com os ajustes na engrenagem
do canto superior direito.

Nada aqui executa lógica de sistema: toda ação chama `core.*` dentro de um
`Worker`, e o retorno chega pela ponte `QtReporter`.
"""

import os

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMessageBox, QPushButton, QStackedWidget,
    QSystemTrayIcon, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

import core
from .boot import BootScreen
from .dialogs import AppDialog, SettingsDialog, WallpaperDialog
from .effects import CRTOverlay, apply_glow
from .enroll import EnrollScreen
from .lockscreen import FalloutLockScreen
from .reporter import QtReporter, Worker
from .sound import SoundPlayer
from .theme import DEFAULT_THEME, build_stylesheet, get_theme


def _panel(title_text=None):
    """Cria um painel com borda e título opcional, e devolve (frame, layout)."""
    frame = QFrame()
    frame.setObjectName("Panel")
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    if title_text is not None:
        title = QLabel(title_text)
        title.setObjectName("PanelTitle")
        outer.addWidget(title)
        frame.title_label = title
    inner = QVBoxLayout()
    inner.setContentsMargins(14, 12, 14, 14)
    inner.setSpacing(10)
    outer.addLayout(inner)
    return frame, inner


class MainWindow(QMainWindow):
    def __init__(self, translator, config, app):
        super().__init__()
        self.t = translator
        self.config = config
        self.app = app
        self.theme_name = config.get("theme", DEFAULT_THEME)
        self.sound = SoundPlayer(config.get("sound_enabled", False))

        self._workers = []      # mantém referência viva enquanto rodam
        self._quitting = False  # distingue "fechar para a bandeja" de "encerrar"

        self.reporter = QtReporter(self.t, self)
        self.reporter.status_changed.connect(self._set_status)
        self.reporter.logged.connect(self._log)

        self.setWindowTitle(self.t("gui_window_title"))
        self.setMinimumSize(1060, 720)
        self._build_ui()
        self._build_tray()

        self.overlay = CRTOverlay(self, self.theme_name)
        self.overlay.raise_()

        self.apply_theme(self.theme_name)
        self.refresh_app_lists()

        self._clock = QTimer(self)
        self._clock.timeout.connect(self._refresh_header_status)
        self._clock.start(20_000)
        self._refresh_header_status()

    # ------------------------------------------------------------------
    # Construção
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.boot_screen = BootScreen(self.t, self.sound, self.theme_name)
        self.boot_screen.finished.connect(self._on_boot_finished)
        self.stack.addWidget(self.boot_screen)

        self.lock_screen = FalloutLockScreen(self.t, self.theme_name, sound=self.sound)
        self.lock_screen.unlocked.connect(self._on_unlocked)
        self.stack.addWidget(self.lock_screen)

        self.enroll_screen = EnrollScreen(self.t, self.sound, self.theme_name)
        self.enroll_screen.submitted.connect(self._on_enrolled)
        self.stack.addWidget(self.enroll_screen)

        self.main_page = QWidget()
        layout = QVBoxLayout(self.main_page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        layout.addLayout(self._build_header())

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_control_tab(), self.t("gui_tab_control"))
        self.tabs.addTab(self._build_database_tab(), self.t("gui_tab_database"))
        layout.addWidget(self.tabs, 1)

        self.stack.addWidget(self.main_page)
        self.stack.setCurrentWidget(self.main_page)

    def _build_header(self):
        row = QHBoxLayout()

        left = QVBoxLayout()
        left.setSpacing(2)
        self.title_label = QLabel(self.t("lumon_industries"))
        self.title_label.setObjectName("Heading")
        self.greeting_label = QLabel()
        self.greeting_label.setObjectName("SubHeading")
        left.addWidget(self.title_label)
        left.addWidget(self.greeting_label)

        right = QVBoxLayout()
        right.setSpacing(6)
        right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.battery_label = QLabel()
        self.battery_label.setObjectName("Dim")
        self.battery_label.setAlignment(Qt.AlignRight)
        right.addWidget(self.battery_label)

        self.lock_button = QPushButton("🔒")
        self.lock_button.setObjectName("IconButton")
        self.lock_button.setFixedWidth(44)
        self.lock_button.setToolTip(self.t("gui_lock_tooltip"))
        # `clicked` entrega um bool posicional; sem a lambda ele viraria `startup`.
        self.lock_button.clicked.connect(lambda: self.lock(startup=False))

        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("IconButton")
        self.settings_button.setFixedWidth(44)
        self.settings_button.setToolTip(self.t("gui_settings_tooltip"))
        self.settings_button.clicked.connect(self.open_settings)

        icons = QHBoxLayout()
        icons.setSpacing(8)
        icons.addStretch(1)
        icons.addWidget(self.lock_button)
        icons.addWidget(self.settings_button)
        right.addLayout(icons)

        row.addLayout(left, 1)
        row.addLayout(right)
        return row

    def _build_control_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        mode_panel, mode_layout = _panel(self.t("active_mode"))
        self.active_mode_label = QLabel()
        self.active_mode_label.setObjectName("StatusValue")
        self.active_mode_label.setAlignment(Qt.AlignCenter)
        mode_layout.addWidget(self.active_mode_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(14)
        self.work_button = QPushButton(self.t("menu_option_1"))
        self.personal_button = QPushButton(self.t("menu_option_2"))
        for button in (self.work_button, self.personal_button):
            button.setObjectName("ModeButton")
            buttons.addWidget(button)
        self.work_button.clicked.connect(lambda: self.start_mode("work"))
        self.personal_button.clicked.connect(lambda: self.start_mode("personal"))
        mode_layout.addLayout(buttons)
        layout.addWidget(mode_panel)

        maint_panel, maint_layout = _panel(self.t("gui_maintenance"))
        self.clean_button = QPushButton(self.t("menu_option_7"))
        self.clean_button.clicked.connect(self.clear_junk)
        maint_layout.addWidget(self.clean_button)
        layout.addWidget(maint_panel)

        log_panel, log_layout = _panel(self.t("gui_log_title"))
        self.status_label = QLabel(self.t("gui_idle"))
        self.status_label.setObjectName("StatusValue")
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        log_layout.addWidget(self.status_label)
        log_layout.addWidget(self.log_view, 1)
        layout.addWidget(log_panel, 1)

        self._mode_buttons = (self.work_button, self.personal_button)
        self._action_buttons = (self.work_button, self.personal_button, self.clean_button)
        return page

    def _build_database_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        panel, panel_layout = _panel(self.t("view_db_title"))

        top = QHBoxLayout()
        self.db_combo = QComboBox()
        self.db_combo.addItem(self.t("work_mode_col"), core.WORK_DB)
        self.db_combo.addItem(self.t("personal_mode_col"), core.PERSONAL_DB)
        self.db_combo.currentIndexChanged.connect(self.refresh_app_lists)
        self.add_button = QPushButton(self.t("gui_add"))
        self.add_button.clicked.connect(self.add_app)
        self.edit_button = QPushButton(self.t("gui_edit"))
        self.edit_button.clicked.connect(self.edit_app)
        self.delete_button = QPushButton(self.t("gui_delete"))
        self.delete_button.setObjectName("Danger")
        self.delete_button.clicked.connect(self.delete_app)
        top.addWidget(self.db_combo, 1)
        top.addWidget(self.add_button)
        top.addWidget(self.edit_button)
        top.addWidget(self.delete_button)
        panel_layout.addLayout(top)

        self.app_list = QListWidget()
        # Duplo clique é o atalho esperado para editar; o botão fica para quem
        # procura a ação na barra.
        self.app_list.itemDoubleClicked.connect(lambda _item: self.edit_app())
        panel_layout.addWidget(self.app_list, 1)

        layout.addWidget(panel, 1)
        return page

    # ------------------------------------------------------------------
    # Abertura
    # ------------------------------------------------------------------
    def play_intro(self):
        """Mostra a abertura ROBCO-LUMON antes de liberar a interface."""
        self.stack.setCurrentWidget(self.boot_screen)
        self.boot_screen.setFocus()
        self.boot_screen.play(self.config.get("user_name", ""))

    def _on_boot_finished(self):
        """Terminada a abertura, decide qual tela entra em cena.

        Sem nome gravado (primeiro uso, `data/` apagada, config corrompido) o
        cadastro vem antes de tudo: a interface só aparece depois de respondido.

        Passado isso, o bloqueio de abertura é de uma vez só: `start_locked`
        começa armado, e resolver o enigma o desarma para sempre (ver
        `_on_unlocked`). Só volta a valer se o usuário rearmar nos ajustes ou
        clicar no cadeado.
        """
        if not self.config.get("user_name"):
            self.stack.setCurrentWidget(self.enroll_screen)
            self.enroll_screen.start()
            return
        self._enter_after_boot()

    def _enter_after_boot(self):
        """Decide entre o bloqueio e a interface, já com o nome garantido."""
        if self.theme_name == "fallout" and self.config.get("start_locked", True):
            self.lock(startup=True)
        else:
            self.stack.setCurrentWidget(self.main_page)

    def _on_enrolled(self, name):
        """Grava o nome informado e libera o restante da inicialização."""
        self.config["user_name"] = name
        core.save_config(self.config)
        self._refresh_header_status()
        self._log(self.t("hello_prepared_for_new_day", user_name=name), "info")
        self._enter_after_boot()

    # ------------------------------------------------------------------
    # Bandeja do sistema
    # ------------------------------------------------------------------
    def _build_tray(self):
        self.tray = QSystemTrayIcon(self._app_icon(), self)
        self._refresh_tray_tooltip()

        menu = QMenu()
        self.show_action = QAction(self.t("gui_tray_show"), self)
        self.show_action.triggered.connect(self._restore_from_tray)
        self.quit_action = QAction(self.t("gui_tray_quit"), self)
        self.quit_action.triggered.connect(self.quit_app)
        menu.addAction(self.show_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)

        self.tray_menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _app_icon(self):
        """Usa logo.ico quando existir; senão desenha um quadrado da cor do tema."""
        icon_path = core.get_asset_path("logo.ico")
        if os.path.exists(icon_path):
            return QIcon(icon_path)

        theme = get_theme(self.theme_name)
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(theme["bg"]))
        painter = QPainter(pixmap)
        painter.setPen(QColor(theme["accent"]))
        painter.drawRect(8, 8, 47, 47)
        painter.end()
        return QIcon(pixmap)

    def _refresh_tray_tooltip(self):
        """Mostra o modo ativo ao passar o mouse sobre o ícone da bandeja."""
        active = self.config.get("active_mode") or self.t("none_mode")
        self.tray.setToolTip(self.t("gui_tray_tooltip", mode_name=active))

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self._restore_from_tray()

    def _restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """O que o X faz depende do ajuste `close_to_tray`.

        Ligado (padrão), esconde na bandeja e encerrar de verdade só pelo menu
        dela. Desligado, o X encerra o programa — daí a chamada a `quit_app`, e
        não um simples `accept()`: sem ela a janela sumiria mas o processo
        continuaria vivo, porque `setQuitOnLastWindowClosed(False)` desliga o
        encerramento automático do Qt.
        """
        if self._quitting:
            event.accept()
            return
        if not self.config.get("close_to_tray", True):
            event.ignore()  # quem encerra é quit_app, no caminho normal de saída
            self.quit_app()
            return
        event.ignore()
        self.hide()
        if self.tray.supportsMessages():
            self.tray.showMessage(
                self.t("gui_tray_minimized_title"),
                self.t("gui_tray_minimized_msg"),
                self._app_icon(),
                4000,
            )

    def quit_app(self):
        self._quitting = True
        self.sound.stop()
        self.tray.hide()
        self.app.quit()

    # ------------------------------------------------------------------
    # Tema e bloqueio
    # ------------------------------------------------------------------
    def apply_theme(self, name):
        self.theme_name = name
        theme = get_theme(name)
        self.app.setStyleSheet(build_stylesheet(name))
        self.overlay.set_theme(name)
        self.overlay.raise_()
        self.boot_screen.set_theme(name)
        self.lock_screen.set_theme(name)
        self.enroll_screen.set_theme(name)

        # O halo precisa ser reaplicado: a cor faz parte do efeito, não do QSS.
        apply_glow(self.title_label, theme["accent"], theme["glow_radius"])
        apply_glow(self.active_mode_label, theme["accent"], theme["glow_radius"] // 2)

        # A tela de bloqueio é uma piada do tema Fallout; fora dele, não faz sentido.
        self.lock_button.setVisible(name == "fallout")
        if name != "fallout" and self.stack.currentWidget() is self.lock_screen:
            self._on_unlocked()

    def lock(self, startup=False):
        """Mostra o terminal ROBCO com um quebra-cabeça novo.

        O enigma da senha é exclusivo do tema Fallout — nos outros temas não há
        o que bloquear.
        """
        if self.theme_name != "fallout":
            return
        self._startup_lock = startup
        self.lock_screen.reset()
        self.stack.setCurrentWidget(self.lock_screen)

    def _on_unlocked(self):
        # Só o bloqueio de ABERTURA se desarma ao ser resolvido; um bloqueio
        # pedido pelo cadeado é avulso e não mexe na configuração.
        if getattr(self, "_startup_lock", False):
            self._startup_lock = False
            self.config["start_locked"] = False
            core.save_config(self.config)
        self.stack.setCurrentWidget(self.main_page)

    # ------------------------------------------------------------------
    # Execução de tarefas do núcleo
    # ------------------------------------------------------------------
    def _run(self, fn, *args, on_done=None, **kwargs):
        """Roda uma função do núcleo numa thread, travando os botões enquanto isso."""
        self._set_buttons_enabled(False)
        self._set_status(self.t("gui_working"))

        worker = Worker(fn, *args, parent=self, **kwargs)

        def finish(result=None):
            self._set_buttons_enabled(True)
            self._set_status(self.t("gui_idle"))
            if worker in self._workers:
                self._workers.remove(worker)
            if on_done is not None and result is not None:
                on_done(result)

        worker.done.connect(finish)
        worker.failed.connect(lambda msg: (self._log(msg, "error"), finish()))
        self._workers.append(worker)
        worker.start()

    def _set_buttons_enabled(self, enabled):
        for button in self._action_buttons:
            button.setEnabled(enabled)

    def _set_status(self, text):
        self.status_label.setText(text)

    def _log(self, message, level="info"):
        theme = get_theme(self.theme_name)
        color = {"error": theme["danger"], "detail": theme["dim"]}.get(level, theme["fg"])
        self.log_view.append(f'<span style="color:{color}">{message}</span>')
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )
        if level == "error":
            self.sound.play("deny")

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------
    def start_mode(self, mode_key):
        """Ativa um modo: grava a escolha, aplica papel de parede e troca os apps."""
        work_apps = core.load_apps(core.WORK_DB)
        personal_apps = core.load_apps(core.PERSONAL_DB)

        if mode_key == "work":
            launch, terminate = work_apps, personal_apps
            mode_name, wallpaper_key = self.t("work_mode"), "work_wallpaper"
        else:
            launch, terminate = personal_apps, work_apps
            mode_name, wallpaper_key = self.t("personal_mode"), "personal_wallpaper"

        # `active_mode` continua guardando o nome traduzido para não quebrar a CLI,
        # mas `active_mode_key` é o campo estável que a GUI usa para comparar —
        # o nome traduzido muda junto com o idioma.
        self.config["active_mode"] = mode_name
        self.config["active_mode_key"] = mode_key
        core.save_config(self.config)
        self._refresh_header_status()

        self._log(self.t("starting_mode", mode_name=mode_name), "info")

        def task():
            core.apply_wallpaper(self.config.get(wallpaper_key), mode_name, self.reporter)
            core.manage_processes(launch, terminate, self.reporter)
            return True

        def done(_result):
            self._log(self.t("mode_activated_successfully", mode_name=mode_name), "info")
            self.sound.play("confirm")

        self._run(task, on_done=done)

    def clear_junk(self):
        self._run(core.clear_system_junk, self.reporter)

    def add_app(self):
        dialog = AppDialog(self.t, self.db_combo.currentData(), self)
        if dialog.exec() != AppDialog.Accepted:
            return
        db_name, app = dialog.result_data()
        apps = core.load_apps(db_name)
        apps.append(app)
        core.save_apps(db_name, apps)
        self._log(self.t("app_added_success", name=app["name"]), "info")

        # Salta para o banco em que o app caiu, para o usuário ver o resultado.
        index = self.db_combo.findData(db_name)
        if index >= 0 and index != self.db_combo.currentIndex():
            self.db_combo.setCurrentIndex(index)
        else:
            self.refresh_app_lists()

    def _selected_app(self):
        """(banco, posição, lista) do item selecionado, ou None.

        Relê o banco do disco em vez de confiar na lista da tela: a CLI pode ter
        mexido nos arquivos enquanto a janela estava aberta. Se a posição não
        existir mais, a lista é recarregada e nada é devolvido.
        """
        item = self.app_list.currentItem()
        if item is None:
            self._log(self.t("gui_no_selection"), "detail")
            return None

        db_name = self.db_combo.currentData()
        position = self.app_list.row(item)
        apps = core.load_apps(db_name)
        if not 0 <= position < len(apps):
            self.refresh_app_lists()
            return None
        return db_name, position, apps

    def edit_app(self):
        selection = self._selected_app()
        if selection is None:
            return
        db_name, position, apps = selection

        dialog = AppDialog(self.t, db_name, self, app=apps[position])
        if dialog.exec() != AppDialog.Accepted:
            self._log(self.t("operation_cancelled"), "detail")
            return

        target_db, app = dialog.result_data()
        index = self.db_combo.findData(target_db)
        if target_db == db_name:
            apps[position] = app
            core.save_apps(db_name, apps)
            self._log(self.t("app_updated_success", name=app["name"]), "info")
        else:
            # Troca de banco: sai de um arquivo e entra no outro.
            apps.pop(position)
            core.save_apps(db_name, apps)
            target_apps = core.load_apps(target_db)
            target_apps.append(app)
            core.save_apps(target_db, target_apps)
            self._log(self.t("app_moved_success", name=app["name"],
                             db=self.db_combo.itemText(index)), "info")

        # Acompanha o app se ele mudou de banco; `setCurrentIndex` já recarrega.
        if index >= 0 and index != self.db_combo.currentIndex():
            self.db_combo.setCurrentIndex(index)
        else:
            self.refresh_app_lists()

    def delete_app(self):
        selection = self._selected_app()
        if selection is None:
            return
        db_name, position, apps = selection

        name = apps[position]["name"]
        confirm = QMessageBox.question(
            self, self.t("delete_app_title"), self.t("delete_confirm_prompt", name=name)
        )
        if confirm != QMessageBox.Yes:
            self._log(self.t("operation_cancelled"), "detail")
            return

        apps.pop(position)
        core.save_apps(db_name, apps)
        self._log(self.t("app_deleted_success", name=name), "info")
        self.refresh_app_lists()

    # --- ajustes ---
    def open_settings(self):
        dialog = SettingsDialog(self.t, self.config, self)
        dialog.theme_preview.connect(self.apply_theme)
        dialog.wallpaper_requested.connect(lambda: self.configure_wallpaper(dialog))
        dialog.restore_requested.connect(self.restore_defaults)
        if dialog.exec() != SettingsDialog.Accepted:
            return

        self.config.update(dialog.result_data())
        core.save_config(self.config)

        self.t.set_language(self.config["language"])
        self.sound.set_enabled(self.config["sound_enabled"])
        self.apply_theme(self.config["theme"])
        self.retranslate()
        self._log(self.t("gui_settings_saved"), "info")

    def configure_wallpaper(self, parent=None):
        dialog = WallpaperDialog(self.t, self.config, parent or self)
        if dialog.exec() != WallpaperDialog.Accepted:
            return
        key, data = dialog.result_data()
        self.config[key] = data
        core.save_config(self.config)
        mode_name = self.t("work_mode") if key == "work_wallpaper" else self.t("personal_mode")
        style_name = dict(WallpaperDialog.STYLES).get(data["style"], "style_fill")
        self._log(self.t("wallpaper_set_success", mode_name=mode_name,
                         style_name=self.t(style_name)), "info")

    def restore_defaults(self):
        confirm = QMessageBox.question(
            self, self.t("restore_title"), self.t("restore_warning")
        )
        if confirm != QMessageBox.Yes:
            self._log(self.t("operation_cancelled"), "detail")
            return
        try:
            for db_file in (core.WORK_DB, core.PERSONAL_DB, core.CONFIG_DB):
                path = core.get_db_path(db_file)
                if os.path.exists(path):
                    os.remove(path)
                    self._log(f"{self.t('removed')}: {db_file}", "detail")
            self._log(self.t("system_restored"), "info")
            QMessageBox.information(self, self.t("restore_title"), self.t("restart_app_prompt"))
            self.quit_app()
        except OSError as e:
            self._log(f"{self.t('error_restoring')}: {e}", "error")

    # ------------------------------------------------------------------
    # Atualização de tela
    # ------------------------------------------------------------------
    def refresh_app_lists(self):
        self.app_list.clear()
        for app in core.load_apps(self.db_combo.currentData()):
            label = app["name"]
            marks = []
            if app.get("requires_admin"):
                marks.append(self.t("app_info_admin").strip())
            if app.get("close_after_launch"):
                marks.append(self.t("gui_close_after_launch"))
            if marks:
                label += "  ·  " + " · ".join(marks)
            self.app_list.addItem(QListWidgetItem(f"{label}\n{app['path']}"))

    def _refresh_header_status(self):
        user = self.config.get("user_name") or "innie"
        self.greeting_label.setText(self.t("welcome_back", user_name=user))

        active = self.config.get("active_mode") or self.t("none_mode")
        self.active_mode_label.setText(active)
        self._refresh_tray_tooltip()

        # Configurações gravadas pela CLI só têm o nome traduzido; nesse caso
        # deduz a chave comparando com os nomes do idioma atual.
        active_key = self.config.get("active_mode_key")
        if not active_key:
            active_key = {self.t("work_mode"): "work",
                          self.t("personal_mode"): "personal"}.get(active)
        for key, button in zip(("work", "personal"), self._mode_buttons):
            button.setProperty("active", "true" if key == active_key else "false")
            # Mudar uma propriedade usada no QSS exige repolir o widget.
            button.style().unpolish(button)
            button.style().polish(button)

        battery = core.get_battery()
        if battery is None:
            self.battery_label.setText(self.t("battery_na"))
        else:
            percent, plugged = battery
            state = self.t("battery_charging") if plugged else self.t("battery_discharging")
            self.battery_label.setText(f"{percent}%  {state}")

    def retranslate(self):
        """Reaplica os textos após troca de idioma."""
        self.setWindowTitle(self.t("gui_window_title"))
        self.title_label.setText(self.t("lumon_industries"))
        self.tabs.setTabText(0, self.t("gui_tab_control"))
        self.tabs.setTabText(1, self.t("gui_tab_database"))
        self.work_button.setText(self.t("menu_option_1"))
        self.personal_button.setText(self.t("menu_option_2"))
        self.clean_button.setText(self.t("menu_option_7"))
        self.add_button.setText(self.t("gui_add"))
        self.edit_button.setText(self.t("gui_edit"))
        self.delete_button.setText(self.t("gui_delete"))
        self.settings_button.setToolTip(self.t("gui_settings_tooltip"))
        self.lock_button.setToolTip(self.t("gui_lock_tooltip"))
        self.db_combo.setItemText(0, self.t("work_mode_col"))
        self.db_combo.setItemText(1, self.t("personal_mode_col"))
        self.show_action.setText(self.t("gui_tray_show"))
        self.quit_action.setText(self.t("gui_tray_quit"))
        self.lock_screen.retranslate()
        self.enroll_screen.retranslate()
        self._refresh_header_status()
        self.refresh_app_lists()
