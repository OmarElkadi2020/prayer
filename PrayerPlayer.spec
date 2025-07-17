# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('src/assets', 'src/assets'), ('src/config', 'src/config')]
binaries = []
hiddenimports = ['src.auth', 'src.calendar_api', 'src.config', 'src.platform', 'src.gui', 'src.state', 'src.tray_icon']


tmp_ret = collect_all('PySide6')

# Filter out QtWebEngine related components
filtered_datas = [d for d in tmp_ret[0] if 'QtWebEngine' not in d[0]]
filtered_binaries = [b for b in tmp_ret[1] if 'QtWebEngine' not in b[0]]
filtered_hiddenimports = [h for h in tmp_ret[2] if 'QtWebEngine' not in h]

datas += filtered_datas
binaries += filtered_binaries
hiddenimports += filtered_hiddenimports


a = Analysis(
    ['src/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
    ],
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
    name='PrayerPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['src/assets/mosque.png'],
)
