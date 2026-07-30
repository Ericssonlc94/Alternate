# -*- mode: python ; coding: utf-8 -*-
#
# Receita de build da CLI:
#     pyinstaller packaging/severance_system.spec
#
# Caminhos ancorados em SPECPATH (a pasta deste arquivo): o PyInstaller resolve
# relativos do .spec a partir dele, entao "src/..." viraria "packaging/src/...".
#
# `pathex` coloca src/ no caminho de busca para que o "import core" do
# severance_system.py resolva; `datas` embarca assets/ (traducoes e logo), que
# o PyInstaller descompacta em sys._MEIPASS — de onde core.get_asset_path() le.
# A pasta data/ NAO entra aqui de proposito: config e bancos de apps sao dados
# do usuario e devem viver ao lado do executavel, nao dentro dele.

import os

ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))
SRC = os.path.join(ROOT, 'src')

# O logo foi removido do repositorio. Referencia-lo direto quebraria o build;
# se voltar, e embarcado e vira o icone do executavel.
ICON = os.path.join(ROOT, 'assets', 'logo.ico')
has_icon = os.path.exists(ICON)

datas = [(os.path.join(ROOT, 'assets', 'lang'), 'assets/lang')]
if has_icon:
    datas.append((ICON, 'assets'))


a = Analysis(
    [os.path.join(SRC, 'severance_system.py')],
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
    name='severance_system',
    icon=ICON if has_icon else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
