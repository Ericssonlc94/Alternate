"""Tela de bloqueio do tema Fallout: o terminal TecCo Termlink.

Reproduz o minigame de senha dos jogos: um despejo de memória com palavras
escondidas no meio de lixo, quatro tentativas, e a dica de "likeness" (quantos
caracteres da palavra escolhida coincidem de posição com a senha). Pares de
parênteses/colchetes na mesma linha funcionam como bônus, removendo uma palavra
errada ou devolvendo as tentativas.

É uma brincadeira, não segurança: qualquer um que abra `config.json` ou rode a
CLI passa por cima disso. O bloqueio nem sequer esconde dados — só atrasa a
janela principal.

Todo o texto do terminal acompanha o idioma configurado (assets/lang/*.json, chaves
`gui_lock_*`); só o nome da corporação permanece como está, por ser marca.
"""

import random

from PySide6.QtCore import QUrl, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QTextBrowser, QVBoxLayout, QWidget,
)

from .effects import apply_glow
from .theme import get_theme

# --- PARÂMETROS DO QUEBRA-CABEÇA ---
ROWS_PER_COLUMN = 17
COLUMNS = 2
CHARS_PER_ROW = 12
MAX_ATTEMPTS = 4
LOCKOUT_SECONDS = 10

GARBAGE = "!@#$%^&*()_-+=.,:;'\"<>[]{}/\\|?"
BRACKET_PAIRS = {"(": ")", "[": "]", "<": ">", "{": "}"}

# Palavras de mesmo comprimento, como no jogo. Agrupadas por tamanho para que a
# dificuldade possa variar sem quebrar o alinhamento das colunas.
WORD_POOL = {
    5: ["ALERT", "AGENT", "BADGE", "BLOCK", "BRAIN", "CHIEF", "CLEAN", "DRIVE",
        "ENTRY", "FLOOR", "GUARD", "LEVEL", "LOGIC", "MOUSE", "NIGHT", "POWER",
        "RADIO", "ROBOT", "STEAM", "TOKEN", "VAULT", "WATER", "WHEEL", "WORLD"],
    6: ["ACCESS", "BUNKER", "CIPHER", "DAMAGE", "ENERGY", "FILTER", "GEIGER",
        "HELMET", "IMPACT", "JACKET", "KEYPAD", "LOCKED", "MEMORY", "NUCLEAR",
        "OUTPUT", "PISTOL", "RADIUS", "SAFETY", "SIGNAL", "SYSTEM", "TARGET",
        "VECTOR", "WINDOW", "WIRING"],
    7: ["ANOMALY", "BATTERY", "CAPSULE", "CIRCUIT", "COMMAND", "CONSOLE",
        "CONTROL", "DEFAULT", "FALLOUT", "MONITOR", "NETWORK", "OVERRIDE",
        "PROGRAM", "PROTOCOL", "RADIATE", "REACTOR", "SECTION", "SEVERED",
        "STORAGE", "TERMINAL", "VERSION", "WARNING"],
}
# Remove o que não bate com o comprimento da chave (erro fácil de cometer ao
# editar as listas acima à mão).
WORD_POOL = {n: [w for w in words if len(w) == n] for n, words in WORD_POOL.items()}


class _Puzzle:
    """Estado de uma rodada: o despejo de memória, as palavras e os bônus."""

    def __init__(self, word_length=6, word_count=10):
        self.word_length = word_length
        pool = WORD_POOL.get(word_length) or WORD_POOL[6]
        self.words = random.sample(pool, min(word_count, len(pool), ROWS_PER_COLUMN * COLUMNS))
        self.password = random.choice(self.words)
        self.removed = set()  # palavras eliminadas por bônus de "dud removal"

        self.rows = [[random.choice(GARBAGE) for _ in range(CHARS_PER_ROW)]
                     for _ in range(ROWS_PER_COLUMN * COLUMNS)]
        self.tokens = {}  # id -> ("word"|"bonus", valor, linha, coluna_inicial, tamanho)

        self._place_words()
        self._place_bonuses()
        self._base_address = random.randrange(0xC000, 0xF000) & 0xFFF0

    def _place_words(self):
        """Cada palavra ocupa um trecho contíguo de UMA linha (nunca quebra)."""
        free_rows = random.sample(range(len(self.rows)), len(self.words))
        for token_id, (word, row) in enumerate(zip(self.words, free_rows)):
            start = random.randint(0, CHARS_PER_ROW - self.word_length)
            self.rows[row][start:start + self.word_length] = list(word)
            self.tokens[f"w{token_id}"] = ("word", word, row, start, self.word_length)

    def _place_bonuses(self):
        """Procura pares de delimitadores em linhas SEM palavra e os torna clicáveis.

        No jogo o par precisa abrir e fechar na mesma linha, com apenas lixo no
        meio — por isso a busca ignora linhas que já receberam uma palavra.
        """
        rows_with_words = {row for _, _, row, _, _ in self.tokens.values()}
        bonus_id = 0
        for row_idx, row in enumerate(self.rows):
            if row_idx in rows_with_words or bonus_id >= 4:
                continue
            for start, char in enumerate(row):
                closer = BRACKET_PAIRS.get(char)
                if not closer:
                    continue
                end = next((i for i in range(start + 1, len(row)) if row[i] == closer), None)
                if end is not None:
                    span = "".join(row[start:end + 1])
                    self.tokens[f"b{bonus_id}"] = ("bonus", span, row_idx, start, end - start + 1)
                    bonus_id += 1
                    break  # no máximo um bônus por linha

    def address(self, row_index):
        return f"0x{self._base_address + row_index * CHARS_PER_ROW:04X}"

    def likeness(self, guess):
        """Quantos caracteres coincidem em POSIÇÃO com a senha."""
        return sum(1 for a, b in zip(guess, self.password) if a == b)

    def active_duds(self):
        return [w for w in self.words if w != self.password and w not in self.removed]


class FalloutLockScreen(QWidget):
    """Terminal TecCo. Emite `unlocked` quando a senha correta é escolhida."""

    unlocked = Signal()

    def __init__(self, translator, theme_name="fallout", parent=None, sound=None):
        super().__init__(parent)
        self._t = translator
        self._sound = sound
        self._theme = get_theme(theme_name)
        self._hovered = None
        self._locked_out = False  # esgotou as tentativas (muda o texto do cabeçalho)
        self._frozen = False      # ignora cliques (lockout OU animação de acerto)

        self._build_ui()
        self.reset()

    # --- construção ---
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(46, 34, 46, 34)
        root.setSpacing(4)

        self.header = QLabel(self._t("gui_lock_header"))
        self.enter_label = QLabel(self._t("gui_lock_enter_password"))
        self.attempts_label = QLabel()
        for lbl in (self.header, self.enter_label, self.attempts_label):
            lbl.setObjectName("Dim")
            root.addWidget(lbl)
        self.header.setObjectName("PanelTitle")
        root.addSpacing(14)

        body = QHBoxLayout()
        body.setSpacing(22)

        self.dump = QTextBrowser()
        self.dump.setOpenLinks(False)
        self.dump.setOpenExternalLinks(False)
        self.dump.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dump.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.dump.setMouseTracking(True)
        self.dump.anchorClicked.connect(self._on_click)
        # `highlighted` tem sobrecarga QUrl/str; fixa a de QUrl para não depender
        # de qual o PySide escolheria.
        self.dump.highlighted[QUrl].connect(self._on_hover)
        body.addWidget(self.dump, 3)

        self.output = QTextBrowser()
        self.output.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.output.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body.addWidget(self.output, 1)

        root.addLayout(body, 1)

        self._apply_glow()

    def _apply_glow(self):
        # O brilho de fósforo vale mais aqui do que em qualquer outra tela.
        apply_glow(self.header, self._theme["fg"], self._theme["glow_radius"])
        apply_glow(self.dump, self._theme["fg"], 10)

    def set_theme(self, theme_name):
        """Acompanha a troca de tema da janela (as cores estão no HTML, não no QSS)."""
        self._theme = get_theme(theme_name)
        self._apply_glow()
        self._render()

    def _play(self, effect):
        if self._sound is not None:
            self._sound.play(effect)

    # --- ciclo do jogo ---
    def reset(self):
        """Sorteia um novo quebra-cabeça e devolve as tentativas."""
        self._puzzle = _Puzzle(word_length=random.choice([5, 6, 7]))
        self._attempts = MAX_ATTEMPTS
        self._history = []
        self._used_bonuses = set()
        self._locked_out = False
        self._frozen = False
        self._hovered = None
        self._render()

    def _on_hover(self, url):
        token = url.toString() or None
        if token != self._hovered:
            self._hovered = token
            self._render()

    def _on_click(self, url):
        if self._frozen:
            return
        token_id = url.toString()
        token = self._puzzle.tokens.get(token_id)
        if not token:
            return
        kind, value, *_ = token

        self._play("key")
        if kind == "bonus":
            self._use_bonus(token_id, value)
        elif value in self._puzzle.removed:
            return  # palavra já eliminada: clique não conta
        else:
            self._guess(value)
        self._render()

    def _use_bonus(self, token_id, span):
        if token_id in self._used_bonuses:
            return
        self._used_bonuses.add(token_id)
        self._log(f">{span}")
        # No jogo, devolver tentativas é o resultado raro.
        duds = self._puzzle.active_duds()
        if random.random() < 0.25 or not duds:
            self._attempts = MAX_ATTEMPTS
            self._log(">" + self._t("gui_lock_allowance"))
        else:
            self._puzzle.removed.add(random.choice(duds))
            self._log(">" + self._t("gui_lock_dud_removed"))

    def _guess(self, word):
        self._log(f">{word}")
        if word == self._puzzle.password:
            self._log(">" + self._t("gui_lock_exact_match"))
            self._log(">" + self._t("gui_lock_accessing"))
            self._play("confirm")
            # Congela os cliques SEM marcar lockout: o cabeçalho deve continuar
            # dizendo "ENTER PASSWORD NOW" durante a saída, não "TERMINAL LOCKED".
            self._frozen = True
            self._render()
            QTimer.singleShot(900, self.unlocked.emit)
            return

        self._attempts -= 1
        self._play("deny")
        self._log(">" + self._t("gui_lock_entry_denied"))
        self._log(">" + self._t("gui_lock_likeness", count=self._puzzle.likeness(word)))
        if self._attempts <= 0:
            self._enter_lockout()

    def _enter_lockout(self):
        """Bloqueio temporário. Como é brincadeira, ele se destrava sozinho."""
        self._locked_out = True
        self._frozen = True
        self._log(">" + self._t("gui_lock_terminal_locked"))
        self._log(">" + self._t("gui_lock_contact_admin"))
        self._remaining = LOCKOUT_SECONDS

        self._countdown = QTimer(self)
        self._countdown.timeout.connect(self._tick_lockout)
        self._countdown.start(1000)
        self._render()

    def _tick_lockout(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._countdown.stop()
            self.reset()
        else:
            self._render()

    def _log(self, line):
        self._history.append(line)
        self._history = self._history[-16:]

    # --- renderização ---
    def _render(self):
        # Os textos são relidos a cada render, então trocar o idioma nos ajustes
        # se reflete aqui sem precisar remontar a tela.
        self.header.setText(self._t("gui_lock_header"))
        if self._locked_out:
            self.enter_label.setText(self._t("gui_lock_retry_in", seconds=self._remaining))
        else:
            self.enter_label.setText(self._t("gui_lock_enter_password"))

        attempts = max(0, self._attempts)
        blocks = " ".join("■" * attempts)
        self.attempts_label.setText(f"{self._t('gui_lock_attempts', count=attempts)} {blocks}")

        self.dump.setHtml(self._dump_html())
        self.output.setHtml(self._output_html())

    def _token_at(self, row_index, col_index):
        """Devolve (id, token) se a posição fizer parte de um trecho clicável."""
        for token_id, token in self._puzzle.tokens.items():
            _, _, row, start, length = token
            if row == row_index and start <= col_index < start + length:
                return token_id, token
        return None, None

    def _dump_html(self):
        fg, accent, dim = self._theme["fg"], self._theme["accent"], self._theme["dim"]
        rows_html = []

        for line in range(ROWS_PER_COLUMN):
            parts = []
            for col in range(COLUMNS):
                row_index = col * ROWS_PER_COLUMN + line
                parts.append(
                    f"<span style='color:{dim}'>{self._puzzle.address(row_index)}</span> "
                    + self._row_html(row_index, fg, accent)
                )
            rows_html.append("  ".join(parts))

        body = "<br>".join(rows_html)
        return (
            f"<pre style='font-family:Cascadia Mono,Consolas,monospace;"
            f"font-size:14px;line-height:150%;color:{fg};margin:0'>{body}</pre>"
        )

    def _row_html(self, row_index, fg, accent):
        """Monta uma linha, envolvendo trechos clicáveis em âncoras."""
        out = []
        col = 0
        while col < CHARS_PER_ROW:
            token_id, token = self._token_at(row_index, col)
            if token is None:
                out.append(_escape(self._puzzle.rows[row_index][col]))
                col += 1
                continue

            kind, value, _row, start, length = token
            text = _escape("".join(self._puzzle.rows[row_index][start:start + length]))
            spent = (kind == "word" and value in self._puzzle.removed) or \
                    (kind == "bonus" and token_id in self._used_bonuses)

            if spent:
                # Palavra eliminada vira lixo, como no jogo.
                out.append(f"<span style='color:{self._theme['accent_dim']}'>"
                           + "." * length + "</span>")
            elif self._hovered == token_id and not self._frozen:
                out.append(f"<a href='{token_id}' style='color:{self._theme['bg']};"
                           f"background-color:{accent};text-decoration:none'>{text}</a>")
            else:
                out.append(f"<a href='{token_id}' style='color:{fg};"
                           f"text-decoration:none'>{text}</a>")
            col = start + length
        return "".join(out)

    def _output_html(self):
        # `div` em vez de `pre`: as frases traduzidas são mais longas que as
        # originais em inglês e precisam quebrar dentro da coluna estreita.
        fg = self._theme["fg"]
        lines = "<br>".join(_escape(line) for line in self._history) or "&gt;"
        return (
            f"<div style='font-family:Cascadia Mono,Consolas,monospace;"
            f"font-size:13px;line-height:160%;color:{fg};margin:0'>{lines}</div>"
        )

    def retranslate(self):
        """Reaplica os textos após troca de idioma."""
        self._render()


def _escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))
