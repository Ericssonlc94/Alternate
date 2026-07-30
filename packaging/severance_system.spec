# -*- mode: python ; coding: utf-8 -*-
#
# Receita de build da CLI. Rode a partir da RAIZ do projeto:
#     pyinstaller packaging/severance_system.spec
# Os caminhos abaixo sao relativos ao diretorio de onde o comando e chamado.
#
# `pathex` coloca src/ no caminho de busca para que o "import core" do
# severance_system.py resolva; `datas` embarca assets/ (traducoes e logo), que
# o PyInstaller descompacta em sys._MEIPASS — de onde core.get_asset_path() le.
# A pasta data/ NAO entra aqui de proposito: config e bancos de apps sao dados
# do usuario e devem viver ao lado do executavel, nao dentro dele.


a = Analysis(
    ['src/severance_system.py'],
    pathex=['src'],
    binaries=[],
    datas=[('assets', 'assets')],
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
    icon='assets/logo.ico',
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
