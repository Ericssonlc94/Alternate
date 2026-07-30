"""Ponto de entrada da GUI como ARQUIVO, para o PyInstaller.

`python -m gui` continua sendo a forma normal de rodar do código-fonte, mas não
serve de alvo para o empacotador: ele analisa um arquivo, e `gui/__main__.py` usa
imports relativos que só resolvem com o pacote já montado. Este script dá o ponto
de entrada absoluto que o `.spec` precisa — e também funciona solto:

    python src/severance_gui.py
"""

from gui.app import main

if __name__ == "__main__":
    main()
