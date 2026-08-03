"""Camada de interface gráfica do Alternate (PySide6).

Este pacote é uma *casca* sobre `core.py`: nenhuma lógica de sistema mora aqui.
A comunicação com o núcleo acontece pelo contrato `core.Reporter`, implementado
em `gui.reporter.QtReporter`.
"""
