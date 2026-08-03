"""Cadastro do usuário no primeiro uso.

Quando não há nome gravado — instalação nova, `data/` apagada, `config.json`
corrompido — a interface principal fica inacessível até o nome ser informado.
É o equivalente gráfico do que a CLI faz ao iniciar sem `user_name`.

A tela é uma PÁGINA do `QStackedWidget`, não um diálogo modal: um diálogo pode
ser fechado no X e deixaria o menu à mostra por trás, sem nome. Sendo página, a
única saída é responder — que é exatamente a regra pedida.

Respondido o nome, a tela encena a liberação (acesso concedido + saudação) antes
de emitir `submitted`, no mesmo tom da abertura Lumen.
"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from .effects import TypewriterLabel, apply_glow
from .theme import get_theme

# Limite generoso, só para impedir que um nome absurdo estoure o cabeçalho.
MAX_NAME = 40

# Ritmo da liberação, em ms. Os mesmos valores da abertura, para as duas
# sequências parecerem o mesmo sistema falando.
PAUSE_BEFORE_GREETING = 260
PAUSE_BEFORE_MENU = 900


class EnrollScreen(QWidget):
    """Pergunta o nome do usuário e emite `submitted` com o valor validado."""

    submitted = Signal(str)

    def __init__(self, translator, sound, theme_name, parent=None):
        super().__init__(parent)
        self._t = translator
        self._sound = sound
        self._theme = get_theme(theme_name)
        self._name = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(60, 40, 60, 40)
        root.setSpacing(0)
        root.addStretch(2)

        # A marca, e não "bem-vindo": a abertura acabou de exibir a saudação, e
        # repeti-la aqui faria as duas telas parecerem a mesma.
        self.title = QLabel(self._t("lumon_industries"))
        self.title.setObjectName("BootBrand")
        self.title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.title)
        root.addSpacing(28)

        # A pergunta é digitada, no mesmo ritmo da abertura, para a transição do
        # boot para o cadastro não parecer troca de programa.
        self.question = TypewriterLabel("", interval=34)
        self.question.setObjectName("BootGreeting")
        self.question.setAlignment(Qt.AlignCenter)
        self.question.char_typed.connect(lambda: self._sound.play("key"))
        self.question.finished.connect(self._on_question_typed)
        root.addWidget(self.question)
        root.addSpacing(20)

        root.addWidget(self._build_form())
        root.addWidget(self._build_result())
        root.addStretch(3)

        self.set_theme(theme_name)

    def _build_form(self):
        """Campo, botão e aviso — some quando o nome é aceito."""
        self.form = QWidget()
        box = QVBoxLayout(self.form)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        field_row = QHBoxLayout()
        field_row.addStretch(1)
        self.field = QLineEdit()
        self.field.setMaxLength(MAX_NAME)
        self.field.setAlignment(Qt.AlignCenter)
        self.field.setFixedWidth(360)
        self.field.setEnabled(False)  # liberado quando a pergunta termina
        self.field.returnPressed.connect(self._submit)
        self.field.textEdited.connect(self._on_edited)
        field_row.addWidget(self.field)
        field_row.addStretch(1)
        box.addLayout(field_row)
        box.addSpacing(14)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.button = QPushButton(self._t("gui_save"))
        self.button.setEnabled(False)
        self.button.clicked.connect(self._submit)
        button_row.addWidget(self.button)
        button_row.addStretch(1)
        box.addLayout(button_row)
        box.addSpacing(10)

        # Ocupa o espaço desde o início: sem isso a tela "pula" ao primeiro erro.
        self.hint = QLabel(" ")
        self.hint.setObjectName("Dim")
        self.hint.setAlignment(Qt.AlignCenter)
        box.addWidget(self.hint)
        return self.form

    def _build_result(self):
        """Acesso concedido e saudação — entram no lugar do formulário."""
        self.result = QWidget()
        self.result.setVisible(False)
        box = QVBoxLayout(self.result)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        self.access = TypewriterLabel("", interval=34)
        self.access.setObjectName("BootAccess")
        self.access.setAlignment(Qt.AlignCenter)
        self.access.finished.connect(self._on_access_typed)
        box.addWidget(self.access)
        box.addSpacing(12)

        self.greeting = TypewriterLabel("", interval=28)
        self.greeting.setObjectName("BootGreeting")
        self.greeting.setAlignment(Qt.AlignCenter)
        self.greeting.char_typed.connect(lambda: self._sound.play("key"))
        self.greeting.finished.connect(self._on_greeting_typed)
        box.addWidget(self.greeting)
        return self.result

    # --- ciclo ---
    def start(self):
        """Começa a perguntar. Chamado quando a página entra em cena."""
        self._name = ""
        self.field.clear()
        self.hint.setText(" ")
        self.field.setEnabled(False)
        self.button.setEnabled(False)
        self.form.setVisible(True)
        self.result.setVisible(False)
        self.access.setText("")
        self.greeting.setText("")
        self.question.start(self._t("what_is_your_name_innie"))

    def _on_question_typed(self):
        self.field.setEnabled(True)
        self.field.setFocus()

    def _on_edited(self, text):
        self.button.setEnabled(bool(text.strip()))
        if text.strip():
            self.hint.setText(" ")

    def _submit(self):
        # `title()` espelha o que a CLI grava, para o mesmo config.json servir aos dois.
        name = self.field.text().strip().title()
        if not name:
            self._sound.play("deny")
            self.hint.setText(self._t("no_name_provided"))
            self.field.setFocus()
            return

        self._name = name
        self.form.setVisible(False)
        self.result.setVisible(True)
        self._sound.play("confirm")
        self.access.start(self._t("access_granted"))

    def _on_access_typed(self):
        QTimer.singleShot(
            PAUSE_BEFORE_GREETING,
            lambda: self.greeting.start(
                self._t("hello_prepared_for_new_day", user_name=self._name)),
        )

    def _on_greeting_typed(self):
        # A saudação fica em cena um instante antes de o menu tomar a tela.
        QTimer.singleShot(PAUSE_BEFORE_MENU, lambda: self.submitted.emit(self._name))

    # --- aparência / idioma ---
    def set_theme(self, theme_name):
        self._theme = get_theme(theme_name)
        apply_glow(self.title, self._theme["accent"], self._theme["glow_radius"])
        apply_glow(self.access, self._theme["accent"], self._theme["glow_radius"] // 2)

    def retranslate(self):
        self.title.setText(self._t("lumon_industries"))
        self.button.setText(self._t("gui_save"))
