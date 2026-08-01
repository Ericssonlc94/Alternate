"""Diálogos de cadastro: aplicativos e papel de parede.

Substituem os fluxos de pergunta-e-resposta da CLI (`add_app_screen`,
`add_wallpaper_screen`) por formulários — todos os campos ficam visíveis ao mesmo
tempo e dá para corrigir um erro sem recomeçar.
"""

import os

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

import core
from .theme import THEMES


class AppDialog(QDialog):
    """Cadastro ou edição de um aplicativo em um dos bancos.

    `result_data()` devolve (nome_do_banco, dicionário_do_app) no formato que
    `core.save_apps` já espera.

    Passando `app`, o formulário abre preenchido e vira edição — inclusive do
    banco: trocar o combo move o aplicativo de TRABALHO para PESSOAL (ou o
    contrário), e quem grava é `MainWindow.edit_app`.
    """

    def __init__(self, translator, default_db=core.WORK_DB, parent=None, app=None):
        super().__init__(parent)
        self._t = translator
        self.setWindowTitle(translator("edit_app_title" if app else "add_app_title"))
        self.setMinimumWidth(520)

        self.db_combo = QComboBox()
        self.db_combo.addItem(translator("work_mode_col"), core.WORK_DB)
        self.db_combo.addItem(translator("personal_mode_col"), core.PERSONAL_DB)
        index = self.db_combo.findData(default_db)
        if index >= 0:
            self.db_combo.setCurrentIndex(index)

        self.name_edit = QLineEdit()
        self.path_edit = QLineEdit()
        browse = QPushButton(translator("gui_browse"))
        browse.clicked.connect(self._browse)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse)

        self.admin_check = QCheckBox(translator("gui_requires_admin"))
        self.close_check = QCheckBox(translator("gui_close_after_launch"))

        if app:
            self.name_edit.setText(app.get("name", ""))
            self.path_edit.setText(app.get("path", ""))
            self.admin_check.setChecked(bool(app.get("requires_admin")))
            self.close_check.setChecked(bool(app.get("close_after_launch")))

        form = QFormLayout()
        form.addRow(translator("gui_target_db"), self.db_combo)
        form.addRow(translator("gui_app_name"), self.name_edit)
        form.addRow(translator("gui_app_path"), path_row)
        form.addRow("", self.admin_check)
        form.addRow("", self.close_check)

        self.error_label = QLabel()
        self.error_label.setObjectName("Dim")
        self.error_label.setWordWrap(True)

        buttons = QDialogButtonBox()
        buttons.addButton(translator("gui_save"), QDialogButtonBox.AcceptRole)
        buttons.addButton(translator("gui_cancel"), QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

    def _browse(self):
        filters = ";;".join([
            f"{self._t('file_dialog_executables')} (*.exe)",
            f"{self._t('file_dialog_vbscript')} (*.vbs)",
            f"{self._t('file_dialog_all_files')} (*)",
        ])
        path, _ = QFileDialog.getOpenFileName(self, self._t("gui_browse"), "", filters)
        if path:
            self.path_edit.setText(os.path.normpath(path))
            if not self.name_edit.text().strip():
                # Sugere o nome a partir do arquivo, como atalho.
                self.name_edit.setText(os.path.splitext(os.path.basename(path))[0].title())

    def _accept(self):
        if not self.name_edit.text().strip() or not self.path_edit.text().strip():
            self.error_label.setText(self._t("name_path_empty_error"))
            return
        self.accept()

    def result_data(self):
        app = {
            "name": self.name_edit.text().strip(),
            "path": self.path_edit.text().strip(),
            "requires_admin": self.admin_check.isChecked(),
            "close_after_launch": self.close_check.isChecked(),
        }
        return self.db_combo.currentData(), app


class SettingsDialog(QDialog):
    """Ajustes do sistema, abertos pela engrenagem do canto superior direito.

    Trocar o tema aqui repinta a janela na hora (`theme_preview`), para o usuário
    ver o efeito antes de decidir; cancelar devolve o tema anterior.
    """

    theme_preview = Signal(str)
    wallpaper_requested = Signal()
    restore_requested = Signal()

    def __init__(self, translator, config, parent=None):
        super().__init__(parent)
        self._t = translator
        self.setWindowTitle(translator("gui_tab_settings"))
        self.setMinimumWidth(520)
        self._initial_theme = config.get("theme", "severance")

        self.name_edit = QLineEdit(config.get("user_name", ""))

        self.lang_combo = QComboBox()
        for code in translator.available:
            self.lang_combo.addItem(code.upper(), code)
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(translator.lang)))

        self.theme_combo = QComboBox()
        for name, data in THEMES.items():
            self.theme_combo.addItem(translator(data["label_key"]), name)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(self._initial_theme)))
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        # Armado por padrão: a primeira abertura no PC pede a senha uma vez.
        # Resolvido o enigma, a janela desarma sozinha (ver `_on_unlocked`), e
        # esta caixa é como o usuário rearma quando quiser.
        self.start_locked_check = QCheckBox(translator("gui_start_locked"))
        self.start_locked_check.setChecked(bool(config.get("start_locked", True)))
        self.sound_check = QCheckBox(translator("gui_sound_effects"))
        self.sound_check.setChecked(bool(config.get("sound_enabled", False)))

        # Ligado por padrão: é o comportamento que o app sempre teve. Desmarcado,
        # o X encerra o programa em vez de escondê-lo na bandeja.
        self.close_to_tray_check = QCheckBox(translator("gui_close_to_tray"))
        self.close_to_tray_check.setChecked(bool(config.get("close_to_tray", True)))

        form = QFormLayout()
        form.addRow(translator("gui_user_name"), self.name_edit)
        form.addRow(translator("gui_language"), self.lang_combo)
        form.addRow(translator("gui_theme"), self.theme_combo)
        form.addRow("", self.sound_check)
        form.addRow("", self.close_to_tray_check)
        form.addRow("", self.start_locked_check)

        wallpaper_button = QPushButton(translator("menu_option_6"))
        wallpaper_button.clicked.connect(self.wallpaper_requested.emit)
        restore_button = QPushButton(translator("gui_restore_defaults"))
        restore_button.setObjectName("Danger")
        restore_button.clicked.connect(self._request_restore)

        extras = QHBoxLayout()
        extras.addWidget(wallpaper_button)
        extras.addStretch(1)
        extras.addWidget(restore_button)

        buttons = QDialogButtonBox()
        buttons.addButton(translator("gui_save"), QDialogButtonBox.AcceptRole)
        buttons.addButton(translator("gui_cancel"), QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(extras)
        layout.addWidget(buttons)

        self._sync_lock_availability()

    def _on_theme_changed(self):
        self.theme_preview.emit(self.theme_combo.currentData())
        self._sync_lock_availability()

    def _sync_lock_availability(self):
        """O enigma da senha é exclusivo do tema Fallout; fora dele a caixa não
        tem efeito, então fica desabilitada em vez de prometer algo que não ocorre."""
        is_fallout = self.theme_combo.currentData() == "fallout"
        self.start_locked_check.setEnabled(is_fallout)

    def _request_restore(self):
        # Fecha antes: a restauração encerra o app, e um diálogo aberto ficaria órfão.
        self.reject()
        self.restore_requested.emit()

    def reject(self):
        # Desfaz a pré-visualização de tema ao cancelar.
        if self.theme_combo.currentData() != self._initial_theme:
            self.theme_preview.emit(self._initial_theme)
        super().reject()

    def result_data(self):
        return {
            "user_name": self.name_edit.text().strip(),
            "language": self.lang_combo.currentData(),
            "theme": self.theme_combo.currentData(),
            "start_locked": self.start_locked_check.isChecked(),
            "sound_enabled": self.sound_check.isChecked(),
            "close_to_tray": self.close_to_tray_check.isChecked(),
        }


class WallpaperDialog(QDialog):
    """Escolhe imagem + estilo de exibição para um dos modos."""

    # Mesmos códigos de `core.WALLPAPER_STYLE_MAP`, com a chave de tradução.
    STYLES = [
        ("1", "style_fill"), ("2", "style_fit"), ("3", "style_stretch"),
        ("4", "style_tile"), ("5", "style_center"), ("6", "style_span"),
    ]

    def __init__(self, translator, config, parent=None):
        super().__init__(parent)
        self._t = translator
        self.setWindowTitle(translator("wallpaper_config_title"))
        self.setMinimumWidth(560)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(translator("work_mode"), "work_wallpaper")
        self.mode_combo.addItem(translator("personal_mode"), "personal_wallpaper")
        self.mode_combo.currentIndexChanged.connect(self._load_mode)

        self.path_edit = QLineEdit()
        browse = QPushButton(translator("gui_browse"))
        browse.clicked.connect(self._browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse)

        self.style_combo = QComboBox()
        for code, key in self.STYLES:
            self.style_combo.addItem(translator(key), code)

        form = QFormLayout()
        form.addRow(translator("select_mode_for_wallpaper"), self.mode_combo)
        form.addRow(translator("image_files"), path_row)
        form.addRow(translator("select_wallpaper_style"), self.style_combo)

        self.error_label = QLabel()
        self.error_label.setObjectName("Dim")
        self.error_label.setWordWrap(True)

        buttons = QDialogButtonBox()
        buttons.addButton(translator("gui_save"), QDialogButtonBox.AcceptRole)
        buttons.addButton(translator("gui_cancel"), QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.error_label)
        layout.addWidget(buttons)

        self._config = config
        self._load_mode()

    def _load_mode(self):
        """Preenche o formulário com o que já está salvo para o modo escolhido."""
        data = self._config.get(self.mode_combo.currentData()) or {}
        self.path_edit.setText(data.get("path", ""))
        index = self.style_combo.findData(data.get("style", "1"))
        self.style_combo.setCurrentIndex(max(0, index))

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self._t("gui_browse"), "", f"{self._t('image_files')} (*.png *.jpg *.jpeg)"
        )
        if path:
            self.path_edit.setText(os.path.normpath(path))

    def _accept(self):
        path = self.path_edit.text().strip()
        if not path:
            self.error_label.setText(self._t("no_file_selected"))
            return
        if os.path.splitext(path)[1].lower() not in (".png", ".jpg", ".jpeg"):
            self.error_label.setText(self._t("invalid_file_format"))
            return
        if not os.path.exists(path):
            self.error_label.setText(self._t("wallpaper_not_found", path=path))
            return
        self.accept()

    def result_data(self):
        """Devolve (chave_no_config, {'path': ..., 'style': ...})."""
        return self.mode_combo.currentData(), {
            "path": self.path_edit.text().strip(),
            "style": self.style_combo.currentData(),
        }
