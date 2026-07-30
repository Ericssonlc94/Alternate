# -*- mode: python ; coding: utf-8 -*-
#
# Receita de build da GUI:
#     pyinstaller packaging/severance_gui.spec
#
# Os caminhos sao ancorados em SPECPATH (a pasta deste arquivo), e nao no
# diretorio de trabalho: o PyInstaller resolve caminhos relativos do .spec a
# partir dele, entao "src/..." viraria "packaging/src/...". Assim o build
# funciona de qualquer lugar.
#
# `pathex` coloca src/ no caminho de busca para o "import core" e o "import gui"
# resolverem. `datas` embarca assets/ (traducoes e, se existir, o logo), que o
# PyInstaller descompacta em sys._MEIPASS — de onde core.get_asset_path() le.
#
# data/ NAO entra aqui de proposito: config e bancos de apps sao do usuario e
# precisam sobreviver ao fechamento. O PyInstaller apaga o _MEIPASS a cada saida,
# entao qualquer coisa gravada la se perderia.

import os

ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
SRC = os.path.join(ROOT, 'src')

# O logo foi removido do repositorio; o build segue sem ele e a GUI desenha um
# icone de reserva. Se voltar, e embarcado e vira o icone do executavel.
ICON = os.path.join(ROOT, 'assets', 'logo.ico')
has_icon = os.path.exists(ICON)

datas = [(os.path.join(ROOT, 'assets', 'lang'), 'assets/lang')]
if has_icon:
    datas.append((ICON, 'assets'))


a = Analysis(
    [os.path.join(SRC, 'severance_gui.py')],
    pathex=[SRC],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SeveranceSystem',
    icon=ICON if has_icon else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Sem console: e uma interface grafica, uma janela preta atras seria ruido.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
