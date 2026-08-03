"""Abertura do sistema: o boot da LUMEN INDUSTRIES.

Recria a sequência que a CLI mostrava (`show_splash_screen` + `crypto_animation`
+ `type_text_effect`) e a funde com a estética de boot corporativo: a marca é
uma corporação única, não uma parceria — como a Weylan-Yutani da Nostromo, em
Alien, é a fusão de duas casas num só logotipo, com lema abaixo.

A marca e as linhas técnicas ficam em inglês de propósito: é identidade visual
corporativa, do mesmo modo que o terminal TecCo. Só o que o sistema *diz* ao
usuário (conectando, credenciais, boas-vindas) é traduzido.
"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from .effects import CryptoRevealLabel, FadeInLabel, TypewriterLabel, apply_glow
from .theme import get_theme

BRAND = "LUMEN INDUSTRIES"
TAGLINE = "BUILDING BETTER WORKERS"
PRODUCT = "ALTERNATE"

# Ruído técnico de boot, no espírito dos terminais da TecCo.
BOOT_LINES = [
    "INITIALIZING LUMEN MF BOOT AGENT v2.3.0",
    "RBIOS-4.02.08.00 52EE5.E7.E8",
    "UPLINK XSHK-4 ................. COMPLETE",
]


class BootScreen(QWidget):
    """Toca a abertura e emite `finished` ao terminar (ou ao ser pulada)."""

    finished = Signal()

    def __init__(self, translator, sound, theme_name, parent=None):
        super().__init__(parent)
        self._t = translator
        self._sound = sound
        self._theme = get_theme(theme_name)
        self._done = False
        self._active = None  # rótulo animando agora (para o clique poder pular)

        root = QVBoxLayout(self)
        root.setContentsMargins(60, 40, 60, 30)
        root.setSpacing(0)

        root.addStretch(1)
        self.stream = QVBoxLayout()
        self.stream.setSpacing(6)
        self.stream.setAlignment(Qt.AlignHCenter)
        root.addLayout(self.stream)
        root.addStretch(2)

        hint_row = QHBoxLayout()
        hint_row.addStretch(1)
        self.hint = QLabel(self._t("gui_boot_skip"))
        self.hint.setObjectName("Dim")
        hint_row.addWidget(self.hint)
        root.addLayout(hint_row)

    # --- roteiro ---
    def play(self, user_name):
        """Monta o roteiro e começa. `user_name` personaliza a saudação.

        Sem nome gravado a abertura NÃO concede acesso: não há a quem conceder
        antes de o usuário se identificar. A verificação de credenciais fica —
        é ela que motiva a pergunta —, mas a liberação passa para o cadastro
        (`gui/enroll.py`), depois do nome informado.
        """
        greeting = (self._t("welcome_back", user_name=user_name) if user_name
                    else self._t("welcome_to_severance"))

        granted = [
            ("line", self._t("access_granted"), "BootAccess"),
            ("sound", "confirm"),
            ("pause", 260),
        ] if user_name else []

        self._script = [
            ("sound", "boot"),
            *[("line", text, "BootLine") for text in BOOT_LINES],
            ("pause", 180),
            # A marca é o momento da abertura: surge devagar e fica em cena.
            # Ela não é apagada — segue visível até o fim da sequência.
            ("fade", BRAND, "BootBrand"),
            ("line", TAGLINE, "BootTagline"),
            ("pause", 1600),
            ("line", self._t("connecting_to_mainframe"), "BootLine"),
            ("pause", 120),
            ("crypto", PRODUCT, "BootTitle"),
            ("pause", 200),
            ("line", self._t("verifying_credentials"), "BootLine"),
            ("pause", 140),
            *granted,
            ("line", greeting, "BootGreeting"),
            ("pause", 700),
        ]
        self._step = 0
        self._advance()

    def _advance(self):
        if self._done:
            return
        if self._step >= len(self._script):
            self._finish()
            return

        action, *args = self._script[self._step]
        self._step += 1

        if action == "pause":
            QTimer.singleShot(args[0], self._advance)
        elif action == "sound":
            self._sound.play(args[0])
            self._advance()
        elif action == "line":
            self._play_line(*args)
        elif action == "crypto":
            self._play_crypto(*args)
        elif action == "fade":
            self._play_fade(*args)

    def _play_line(self, text, role):
        # As linhas técnicas correm rápido (são ruído); o que o sistema diz ao
        # usuário é digitado num ritmo legível.
        label = TypewriterLabel(interval=11 if role == "BootLine" else 20)
        label.setObjectName(role)
        label.setAlignment(Qt.AlignCenter)
        if role in ("BootBrand", "BootTitle", "BootAccess"):
            apply_glow(label, self._theme["accent"], self._theme["glow_radius"])
        self.stream.addWidget(label)

        # Um bipe a cada dois caracteres: a cada um vira ruído contínuo.
        counter = {"n": 0}

        def blip():
            counter["n"] += 1
            if counter["n"] % 2 == 0:
                self._sound.play("key")

        label.char_typed.connect(blip)
        label.finished.connect(self._advance)
        self._active = label
        label.start(text)

    def _play_fade(self, text, role):
        """A marca da corporação surge por transparência — sem som e sem ruído."""
        widget = FadeInLabel(
            text,
            duration=2400,
            glow=(self._theme["accent"], self._theme["glow_radius"] + 6),
        )
        widget.setObjectName(role)
        self.stream.addWidget(widget)
        widget.finished.connect(self._advance)
        self._active = widget
        widget.start()

    def _play_crypto(self, text, role):
        label = CryptoRevealLabel(scrambles=3, step_ms=24)
        label.setObjectName(role)
        label.setAlignment(Qt.AlignCenter)
        apply_glow(label, self._theme["accent"], self._theme["glow_radius"] + 6)
        self.stream.addWidget(label)

        label.char_locked.connect(lambda: self._sound.play("scramble"))
        label.finished.connect(self._advance)
        self._active = label
        label.start(text)

    # --- pular ---
    def mousePressEvent(self, _event):
        self.skip()

    def keyPressEvent(self, _event):
        self.skip()

    def skip(self):
        """Encerra a abertura na hora, sem esperar o resto do roteiro."""
        if self._done:
            return
        # Marca ANTES de completar o rótulo: `finish()` dispara `finished`, que
        # chamaria `_advance` e emendaria a próxima etapa do roteiro.
        self._done = True
        if self._active is not None:
            self._active.finish()
        self._sound.stop()
        self.finished.emit()

    def _finish(self):
        if self._done:
            return
        self._done = True
        self.finished.emit()

    def set_theme(self, theme_name):
        self._theme = get_theme(theme_name)
