# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_all
from PySide6 import QtCore

# --- Common Configuration ---
datas = [('src/assets', 'src/assets'), ('src/config', 'src/config')]
binaries = []
hiddenimports = [
    'src.auth', 'src.calendar_api', 'src.config', 'src.platform',
    'src.gui', 'src.state', 'src.tray_icon'
]

# --- Platform-Specific Configuration ---
if sys.platform == 'darwin':
    # On macOS, explicitly include the QtWebEngineCore framework as a binary
    # to handle symlink issues correctly.
    qt_web_engine_path = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.LibrariesPath)
    binaries += [(f'{qt_web_engine_path}/QtWebEngineCore.framework', 'PySide6/Qt/lib')]
    hiddenimports += collect_submodules('PySide6.Qt.plugins.platforms')
elif sys.platform == 'linux':
    hiddenimports += collect_submodules('PySide6.Qt.plugins.xcbglintegrations')

# Collect all other PySide6 data
tmp_ret = collect_all('PySide6')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# --- PyInstaller Analysis ---
a = Analysis(
    ['src/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    icon='src/assets/mosque.png',
)

# --- macOS App Bundle ---
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='PrayerPlayer.app',
        icon='src/assets/mosque.png',
        bundle_identifier=None,
    )
