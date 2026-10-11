# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build spec — one self-contained executable per OS.
# Build:  pyinstaller rubripdf.spec
# Bundles the templates, static assets, fonts and the sample config; app.py
# resolves them from sys._MEIPASS when frozen (see BASE_DIR in app.py).

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('fonts', 'fonts'),
        ('help', 'help'),
        ('example-config.json', '.'),
    ],
    # These are imported lazily inside functions; list them so PyInstaller
    # always bundles them (and their submodules) regardless of code paths.
    hiddenimports=['bs4', 'openpyxl', 'xlrd', 'pypdf', 'waitress'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RubriPDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
