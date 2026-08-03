"""Efeitos visuais: brilho de fósforo, scanlines, varredura e digitação.

O overlay de CRT é um widget transparente que fica *por cima* de toda a janela,
sem interceptar cliques. As scanlines são desenhadas com uma textura de poucos
pixels repetida pelo Qt em vez de um laço de linhas a cada quadro — a diferença
de custo é grande numa janela grande a 25 fps.
"""

import random
import string

from PySide6.QtCore import (
    QEasingCurve, QEvent, QTimer, QVariantAnimation, Qt, Signal,
)
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QWidget

from .theme import get_theme


def apply_glow(widget, color, radius=18):
    """Aplica o halo de fósforo característico dos monitores antigos.

    Um `QGraphicsDropShadowEffect` sem deslocamento vira brilho em volta do texto.
    Cada widget só comporta um efeito gráfico por vez — chamar de novo substitui.
    """
    glow = QGraphicsDropShadowEffect(widget)
    glow.setColor(QColor(color))
    glow.setBlurRadius(radius)
    glow.setOffset(0, 0)
    widget.setGraphicsEffect(glow)
    return glow


class CRTOverlay(QWidget):
    """Camada de vidro sobre a janela: scanlines + vinheta + varredura.

    Uso: `overlay = CRTOverlay(janela, "fallout")`. Ele se redimensiona sozinho
    junto do pai e nunca rouba eventos do mouse.
    """

    FPS_MS = 40

    def __init__(self, parent, theme_name):
        super().__init__(parent)
        # Deixa passar cliques e não pinta fundo próprio.
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._scanlines = None  # QPixmap-textura, recriada quando o tema muda
        self._sweep_pos = 0.0
        self._flicker = 0

        self.set_theme(theme_name)
        parent.installEventFilter(self)
        self.resize(parent.size())

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(self.FPS_MS)

    # --- ciclo de vida ---
    def set_theme(self, theme_name):
        self._theme = get_theme(theme_name)
        self._scanlines = None  # força reconstrução da textura na próxima pintura
        self.update()

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type() == QEvent.Resize:
            self.resize(event.size())
        return False

    def _tick(self):
        if not self.isVisible():
            return
        if self._theme["sweep"]:
            # Uma varredura lenta atravessa a tela a cada ~7 s.
            self._sweep_pos = (self._sweep_pos + 0.006) % 1.4
        if self._theme["flicker"]:
            # Oscilação de brilho: quase sempre zero, com picos esporádicos.
            self._flicker = random.randint(0, 8) if random.random() < 0.12 else 0
        self.update()

    # --- pintura ---
    def _scanline_texture(self):
        """Textura de 1 x gap px: uma linha escura e o resto transparente."""
        gap = self._theme["scanline_gap"]
        pix = QPixmap(1, gap)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.fillRect(0, 0, 1, 1, QColor(0, 0, 0, self._theme["scanline_alpha"]))
        p.end()
        return pix

    def paintEvent(self, _event):
        if self._scanlines is None:
            self._scanlines = self._scanline_texture()

        p = QPainter(self)
        rect = self.rect()

        # 1. Scanlines (textura repetida pelo Qt — barato).
        p.drawTiledPixmap(rect, self._scanlines)

        # 2. Varredura: banda clara descendo devagar.
        if self._theme["sweep"]:
            band_h = max(60, rect.height() // 6)
            y = self._sweep_pos * (rect.height() + band_h) - band_h
            grad = QLinearGradient(0, y, 0, y + band_h)
            tint = QColor(self._theme["accent"])
            tint.setAlpha(0)
            grad.setColorAt(0.0, tint)
            mid = QColor(self._theme["accent"])
            mid.setAlpha(14)
            grad.setColorAt(0.5, mid)
            grad.setColorAt(1.0, tint)
            p.fillRect(rect, grad)

        # 3. Vinheta: escurece os cantos como o vidro curvo de um CRT.
        vignette = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.75)
        vignette.setColorAt(0.0, QColor(0, 0, 0, 0))
        vignette.setColorAt(0.65, QColor(0, 0, 0, 30))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 120))
        p.fillRect(rect, vignette)

        # 4. Oscilação do tubo.
        if self._flicker:
            p.fillRect(rect, QColor(255, 255, 255, self._flicker))
        p.end()


class FadeInLabel(QLabel):
    """Rótulo que surge por transparência, em vez de ser digitado ou decodificado.

    A transparência NÃO usa `QGraphicsOpacityEffect`: o Qt aceita um único efeito
    gráfico por widget e não pinta efeitos aninhados — combinar opacidade com o
    halo de fósforo fazia o texto sumir assim que a animação terminava. Em vez
    disso, anima-se o alfa da cor do texto (via folha de estilo do próprio
    widget) e o alfa do halo, deixando o único efeito gráfico livre para o brilho.
    """

    finished = Signal()

    def __init__(self, text="", parent=None, duration=1100, glow=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)

        self._color = QColor(glow[0]) if glow else QColor(255, 255, 255)
        self._glow = None
        if glow is not None:
            color, radius = glow
            self._glow = apply_glow(self, color, radius)

        self._animation = QVariantAnimation(self)
        self._animation.setDuration(duration)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        # Emerge devagar e se firma no fim, como um tubo esquentando.
        self._animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._animation.valueChanged.connect(self._apply_alpha)
        self._animation.finished.connect(self.finished.emit)

        self._apply_alpha(0.0)

    def _apply_alpha(self, progress):
        r, g, b = self._color.red(), self._color.green(), self._color.blue()
        alpha = max(0.0, min(1.0, float(progress)))
        # A folha de estilo do próprio widget vence a da aplicação para `color`,
        # preservando corpo e espaçamento definidos pelo objectName no tema.
        self.setStyleSheet(f"color: rgba({r}, {g}, {b}, {alpha:.3f});")
        if self._glow is not None:
            halo = QColor(self._color)
            halo.setAlphaF(alpha)
            self._glow.setColor(halo)

    def start(self, text=None):
        if text is not None:
            self.setText(text)
        self._animation.start()

    def finish(self):
        """Salta para o fim (usado quando a abertura é pulada)."""
        self._animation.stop()
        self._apply_alpha(1.0)


class CryptoRevealLabel(QLabel):
    """Decodificação caractere a caractere: o texto se firma da esquerda para a
    direita enquanto o resto continua embaralhando.

    É a `crypto_animation` que a antiga CLI fazia com `rich.Live`, reescrita
    sobre um QTimer — mesmo ritmo: 5 embaralhadas por caractere antes de fixá-lo.
    """

    finished = Signal()
    char_locked = Signal()  # um caractere parou de embaralhar (gancho de som)

    CHARS = string.ascii_uppercase + string.digits + "!@#$%^&*"

    def __init__(self, text="", parent=None, scrambles=5, step_ms=40):
        super().__init__(parent)
        self._full = text
        self._locked = []
        self._index = 0
        self._scramble = 0
        # O custo total é len(texto) x scrambles x step_ms — os padrões copiam a
        # CLI (5 x 40 ms), mas uma abertura que roda todo dia pede menos.
        self._scrambles = scrambles
        self._step_ms = step_ms
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self, text=None):
        if text is not None:
            self._full = text
        self._locked = [""] * len(self._full)
        self._index = 0
        self._scramble = 0
        self._timer.start(self._step_ms)

    def finish(self):
        self._timer.stop()
        self.setText(self._full)

    @property
    def is_running(self):
        return self._timer.isActive()

    def _tick(self):
        if self._index >= len(self._full):
            self._timer.stop()
            self.setText(self._full)
            self.finished.emit()
            return

        # Espaços não embaralham: fixam de imediato, como na versão da CLI.
        if self._full[self._index] == " ":
            self._locked[self._index] = " "
            self._index += 1
            return

        if self._scramble < self._scrambles:
            frame = list(self._locked)
            for j in range(self._index, len(self._full)):
                if self._full[j] != " ":
                    frame[j] = random.choice(self.CHARS)
            self.setText("".join(frame))
            self._scramble += 1
        else:
            self._locked[self._index] = self._full[self._index]
            self.setText("".join(self._locked))
            self._index += 1
            self._scramble = 0
            self.char_locked.emit()


class TypewriterLabel(QLabel):
    """QLabel que revela o texto caractere a caractere, com cursor piscando.

    Usado nas telas de abertura e no terminal do tema Fallout.
    """

    finished = Signal()
    char_typed = Signal()  # gancho de som, um disparo por caractere

    def __init__(self, text="", parent=None, interval=28, cursor="_"):
        super().__init__(parent)
        self._full = text
        self._shown = 0
        self._cursor = cursor
        self._cursor_on = True

        self._type_timer = QTimer(self)
        self._type_timer.timeout.connect(self._advance)
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink)
        self._interval = interval

    def start(self, text=None):
        if text is not None:
            self._full = text
        self._shown = 0
        self._render()
        self._type_timer.start(self._interval)
        self._blink_timer.start(450)

    def finish(self):
        """Revela tudo de uma vez (ex.: o usuário clicou para pular)."""
        was_typing = self._type_timer.isActive()
        self._type_timer.stop()
        self._shown = len(self._full)
        self._render()
        if was_typing:
            self.finished.emit()

    @property
    def is_typing(self):
        return self._type_timer.isActive()

    def _advance(self):
        self._shown += 1
        done = self._shown >= len(self._full)
        if done:
            self._shown = len(self._full)
            self._type_timer.stop()
        self._render()
        self.char_typed.emit()
        if done:
            self.finished.emit()

    def _blink(self):
        self._cursor_on = not self._cursor_on
        self._render()

    def _render(self):
        tail = self._cursor if self._cursor_on else " "
        self.setText(self._full[: self._shown] + tail)
