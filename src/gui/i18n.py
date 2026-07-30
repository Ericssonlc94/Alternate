"""Tradução para a GUI.

Reaproveita `core.load_translations()` (assets/lang/*.json), mas resolve dois problemas
que a CLI não tinha:

1. Estado de idioma sem variável global — a GUI troca de idioma em runtime.
2. As strings do JSON foram escritas para o `rich` e carregam marcação como
   `[bold red]...[/bold red]`, que apareceria literalmente num QLabel.
"""

import re

import core

# Casa marcação do rich (`[bold]`, `[/bold red]`, `[dim]`) sem tocar em textos
# legítimos como "digite [0] para voltar", que começam com dígito.
_RICH_TAG = re.compile(r"\[/?[a-zA-Z][a-zA-Z0-9 _#]*\]")


def strip_markup(text):
    """Remove marcação do rich de uma string vinda dos arquivos de idioma."""
    return _RICH_TAG.sub("", text)


class Translator:
    """Tabela de tradução ativa. Instância única compartilhada pela GUI.

    Uso: `t = Translator("pt")` e depois `t("started")` ou
    `t("apps_launched", count=3)`.
    """

    FALLBACK = "pt"

    def __init__(self, lang=None):
        self._tables = core.load_translations()
        self.lang = lang or self.FALLBACK

    @property
    def available(self):
        """Códigos de idioma encontrados em assets/lang/*.json (ex.: ['en', 'pt'])."""
        return sorted(self._tables)

    def set_language(self, lang):
        if lang in self._tables:
            self.lang = lang

    def __call__(self, key, **kwargs):
        table = self._tables.get(self.lang) or self._tables.get(self.FALLBACK) or {}
        raw = table.get(key)
        if raw is None:
            # Chave ausente aparece visível em vez de quebrar a interface.
            return f"<{key}>"
        try:
            return strip_markup(raw).format(**kwargs)
        except (KeyError, IndexError):
            # Placeholder sem valor correspondente: mostra o texto cru.
            return strip_markup(raw)
