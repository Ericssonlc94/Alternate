"""Ponto de entrada da GUI: `python -m gui`."""

import sys

from PySide6.QtWidgets import QApplication

import core
from .i18n import Translator
from .main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Alternate")

    # Sem isto, esconder a janela na bandeja encerraria o programa: para o Qt,
    # a última janela visível ter sumido é motivo de saída.
    app.setQuitOnLastWindowClosed(False)

    config = core.load_config()
    translator = Translator(config.get("language", "pt"))

    window = MainWindow(translator, config, app)
    window.show()

    # A abertura Lumen roda primeiro; ao terminar, ela mesma decide se cai
    # na tela de bloqueio (tema Fallout com `start_locked`) ou direto na interface.
    window.play_intro()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
