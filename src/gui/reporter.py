"""Ponte entre o núcleo e a interface Qt.

`core.manage_processes` e companhia são funções bloqueantes (contêm `time.sleep`,
varrem processos, mexem no registro). Rodá-las na thread da interface congelaria
a janela — por isso elas são executadas num `Worker`, e os eventos do
`core.Reporter` viram *signals* Qt, que o Qt entrega com segurança na thread da
interface.
"""

from PySide6.QtCore import QObject, QThread, Signal

import core


class QtReporter(QObject, core.Reporter):
    """Implementação de `core.Reporter` que reemite os eventos como signals.

    O núcleo entrega CHAVES i18n; a tradução acontece aqui, antes de emitir, de
    modo que a janela só recebe texto pronto para exibir.
    """

    status_changed = Signal(str)
    logged = Signal(str, str)  # (mensagem, nível: info|detail|error)

    def __init__(self, translator, parent=None):
        QObject.__init__(self, parent)
        self._t = translator

    def status(self, key, **kwargs):
        self.status_changed.emit(self._t(key, **kwargs))

    def info(self, key, **kwargs):
        self.logged.emit(self._t(key, **kwargs), "info")

    def detail(self, key, subject=None, **kwargs):
        label = self._t(key, **kwargs)
        self.logged.emit(f"{label}: {subject}" if subject else label, "detail")

    def error(self, key, subject=None, **kwargs):
        label = self._t(key, **kwargs)
        self.logged.emit(f"{label}: {subject}" if subject else label, "error")


class Worker(QThread):
    """Executa uma função do núcleo fora da thread da interface.

    `done` carrega o valor de retorno (ex.: a tupla de
    `clean_orphan_virtual_desktops`); `failed` carrega a mensagem de uma exceção
    inesperada, para que uma falha no motor nunca derrube a janela.
    """

    done = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args, parent=None, **kwargs):
        super().__init__(parent)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            self.done.emit(self._fn(*self._args, **self._kwargs))
        except Exception as e:  # noqa: BLE001 - a interface precisa sobreviver a qualquer falha
            self.failed.emit(f"{type(e).__name__}: {e}")
