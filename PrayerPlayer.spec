# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

import os
import PySide6

pyside6_path = os.path.dirname(PySide6.__file__)
qt_plugins_path = os.path.join(pyside6_path, 'Qt', 'plugins')
platforms_plugin_path = os.path.join(qt_plugins_path, 'platforms')
xcbglintegrations_plugin_path = os.path.join(qt_plugins_path, 'xcbglintegrations')



datas = [
    ('src/assets', 'src/assets'),
    ('src/config', 'src/config'),
    (platforms_plugin_path, 'PySide6/Qt/plugins/platforms'),
    (xcbglintegrations_plugin_path, 'PySide6/Qt/plugins/xcbglintegrations')
]

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
