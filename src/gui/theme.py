"""Temas visuais da GUI.

Cada tema é uma paleta + alguns parâmetros de efeito. A folha de estilo é uma
única `string.Template` compartilhada: os dois temas divergem por cor, fonte e
raio de borda, não por regras diferentes — assim um ajuste de layout vale para
ambos automaticamente.

`string.Template` (`$var`) em vez de `str.format`, porque QSS usa chaves `{}`
para tudo e `format` engasgaria em cada bloco de regra.
"""

from string import Template

# --- PALETAS ---
THEMES = {
    "severance": {
        "label_key": "gui_theme_severance",
        # Azul-petróleo da Lumen: o mesmo #001E29 que a CLI usava, agora com
        # uma escala de apoio para painéis e bordas.
        "bg": "#001E29",
        "panel": "#00293A",
        "panel_alt": "#013449",
        "border": "#0A5C7A",
        "fg": "#E8F6FB",
        "dim": "#7FA9BA",
        "accent": "#67E8F9",
        "accent_dim": "#1D7F96",
        "danger": "#FF6B6B",
        "ok": "#67E8F9",
        "font": "Consolas, 'Cascadia Mono', monospace",
        "radius": "2px",
        # Efeitos: a estética da série é limpa e nítida — brilho suave, quase
        # nenhuma scanline.
        "glow_radius": 12,
        "scanline_alpha": 16,
        "scanline_gap": 4,
        "flicker": False,
        "sweep": True,
    },
    "fallout": {
        "label_key": "gui_theme_fallout",
        # Fósforo verde do Pip-Boy sobre CRT quase preto.
        "bg": "#031A03",
        "panel": "#06260A",
        "panel_alt": "#093311",
        "border": "#1E7A26",
        "fg": "#41FF00",
        "dim": "#1F8A12",
        "accent": "#7CFF4D",
        "accent_dim": "#1E7A26",
        "danger": "#FF9E3D",
        "ok": "#41FF00",
        "font": "'Cascadia Mono', Consolas, monospace",
        "radius": "0px",
        # Monitor velho: brilho forte, scanlines densas e uma oscilação sutil.
        "glow_radius": 22,
        "scanline_alpha": 44,
        "scanline_gap": 3,
        "flicker": True,
        "sweep": True,
    },
}

DEFAULT_THEME = "severance"


def get_theme(name):
    """Devolve a paleta do tema pedido, caindo no padrão se o nome for inválido."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])


_QSS = Template("""
QWidget {
    background-color: $bg;
    color: $fg;
    font-family: $font;
    font-size: 13px;
}

QMainWindow, QDialog { background-color: $bg; }

/* Sem isto o rótulo pinta o fundo da janela por cima do painel, e um texto
   solto passa a parecer um campo de formulário vazio. */
QLabel { background: transparent; }
QCheckBox { background: transparent; }

/* --- Painéis --- */
QFrame#Panel {
    background-color: $panel;
    border: 1px solid $border;
    border-radius: $radius;
}
QLabel#PanelTitle {
    color: $accent;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 2px;
    padding: 6px 10px;
    border-bottom: 1px solid $border;
}
QLabel#Heading {
    color: $accent;
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 6px;
}
QLabel#SubHeading { color: $dim; letter-spacing: 2px; }

/* --- Abertura (boot LUMEN) --- */
QLabel#BootLine { color: $dim; font-size: 13px; letter-spacing: 1px; }
QLabel#BootBrand {
    color: $accent;
    font-size: 30px;
    font-weight: bold;
    letter-spacing: 10px;
    padding: 10px 0 2px 0;
}
QLabel#BootTagline {
    color: $dim;
    font-size: 12px;
    letter-spacing: 6px;
    padding-bottom: 16px;
}
QLabel#BootTitle {
    color: $fg;
    font-size: 24px;
    font-weight: bold;
    letter-spacing: 8px;
    padding: 12px 0;
}
QLabel#BootAccess { color: $accent; font-size: 15px; letter-spacing: 4px; }
QLabel#BootGreeting { color: $fg; font-size: 15px; letter-spacing: 2px; padding-top: 8px; }
QLabel#StatusValue { color: $fg; font-weight: bold; letter-spacing: 2px; }
QLabel#Dim { color: $dim; }

/* --- Botões --- */
QPushButton {
    background-color: $panel;
    color: $fg;
    border: 1px solid $border;
    border-radius: $radius;
    padding: 9px 16px;
    letter-spacing: 1px;
}
QPushButton:hover { background-color: $panel_alt; border-color: $accent; color: $accent; }
QPushButton:pressed { background-color: $accent_dim; color: $bg; }
QPushButton:disabled { color: $accent_dim; border-color: $accent_dim; }

QPushButton#ModeButton {
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 3px;
    padding: 26px 18px;
    text-align: center;
}
QPushButton#ModeButton[active="true"] {
    background-color: $accent_dim;
    border: 1px solid $accent;
    color: $fg;
}
/* Botões de ícone do cabeçalho (engrenagem, cadeado): quadrados e discretos. */
QPushButton#IconButton {
    padding: 6px 0;
    font-size: 15px;
    letter-spacing: 0;
}
QPushButton#Danger { color: $danger; border-color: $danger; }
QPushButton#Danger:hover { background-color: $danger; color: $bg; }

/* --- Entradas --- */
QLineEdit, QComboBox, QSpinBox {
    background-color: $bg;
    border: 1px solid $border;
    border-radius: $radius;
    padding: 7px 9px;
    selection-background-color: $accent_dim;
    selection-color: $fg;
}
QLineEdit:focus, QComboBox:focus { border-color: $accent; }
QComboBox::drop-down { border: none; width: 22px; }
/* QSS não desenha formas; um triângulo se faz com bordas de um elemento
   de tamanho zero — sem isso o combo fica igual a um campo de texto. */
QComboBox::down-arrow {
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid $accent;
}
QComboBox QAbstractItemView {
    background-color: $panel;
    border: 1px solid $accent;
    selection-background-color: $accent_dim;
    outline: none;
}

QCheckBox { spacing: 9px; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid $border;
    background-color: $bg;
}
QCheckBox::indicator:checked { background-color: $accent; border-color: $accent; }

/* --- Listas e log --- */
QListWidget, QTextEdit, QPlainTextEdit {
    background-color: $bg;
    border: 1px solid $border;
    border-radius: $radius;
    padding: 4px;
    selection-background-color: $accent_dim;
    selection-color: $fg;
}
QListWidget::item { padding: 6px 8px; border-bottom: 1px solid $panel_alt; }
QListWidget::item:selected { background-color: $accent_dim; color: $fg; }

/* --- Abas --- */
QTabWidget::pane { border: 1px solid $border; border-radius: $radius; top: -1px; }
QTabBar::tab {
    background-color: $bg;
    color: $dim;
    border: 1px solid $border;
    border-bottom: none;
    padding: 9px 22px;
    letter-spacing: 2px;
}
QTabBar::tab:selected { background-color: $panel; color: $accent; }
QTabBar::tab:hover { color: $fg; }

/* --- Barra de rolagem --- */
QScrollBar:vertical { background: $bg; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: $accent_dim; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: $accent; }
QScrollBar:horizontal { background: $bg; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: $accent_dim; min-width: 24px; }
QScrollBar::handle:horizontal:hover { background: $accent; }
/* Sem estas quatro, o Qt desenha setas e trilho no tema nativo (claro). */
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: $bg; }

QToolTip {
    background-color: $panel;
    color: $fg;
    border: 1px solid $accent;
    padding: 4px;
}

QMenu { background-color: $panel; border: 1px solid $border; }
QMenu::item { padding: 7px 22px; }
QMenu::item:selected { background-color: $accent_dim; color: $fg; }
""")


def build_stylesheet(name):
    """Monta a folha de estilo completa para o tema indicado."""
    return _QSS.substitute(get_theme(name))
