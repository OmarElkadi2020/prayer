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
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DRender',
        'PySide6.QtBluetooth',
        'PySide6.QtCharts',
        'PySide6.QtConcurrent',
        'PySide6.QtDataVisualization',
        'PySide6.QtDesigner',
        'PySide6.QtHelp',
        'PySide6.QtLocation',
        'PySide6.QtNetworkAuth',
        'PySide6.QtNfc',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtPositioning',
        'PySide6.QtPrintSupport',
        'PySide6.QtQuick',
        'PySide6.QtQuick3D',
        'PySide6.QtQuickControls2',
        'PySide6.QtQuickWidgets',
        'PySide6.QtRemoteObjects',
        'PySide6.QtScxml',
        'PySide6.QtSensors',
        'PySide6.QtSerialBus',
        'PySide6.QtSerialPort',
        'PySide6.QtSql',
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtTest',
        'PySide6.QtWebChannel',
        'PySide6.QtWebSockets',
        'PySide6.QtWebView',
        'PySide6.QtXml',
        'PySide6.QtXmlPatterns',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

import platform
import os

# Set the runtime temporary directory based on the operating system
if platform.system() == "Windows":
    runtime_tmpdir = None  # Use the default temp directory on Windows
else:
    runtime_tmpdir = '/tmp/pyinstaller'  # Use a dedicated directory on Linux/macOS

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PrayerPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['src/assets/mosque.png'],
)
