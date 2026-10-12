# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('packs', 'packs')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5.QtQuick', 'PyQt5.QtQml', 'PyQt5.QtPdf', 'PyQt5.QtPdfWidgets', 'PyQt5.QtNetwork', 'PyQt5.QtSql', 'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets', 'PyQt5.QtXml', 'PyQt5.QtXmlPatterns', 'PyQt5.QtTest', 'PyQt5.QtDesigner', 'PyQt5.QtOpenGL', 'PyQt5.QtPrintSupport', 'PyQt5.Qt3DCore', 'PyQt5.Qt3DRender', 'PyQt5.Qt3DInput', 'PyQt5.Qt3DLogic', 'PyQt5.Qt3DAnimation', 'PyQt5.Qt3DExtras', 'PyQt5.QtSensors', 'PyQt5.QtSerialPort', 'PyQt5.QtWebSockets', 'PyQt5.QtBluetooth', 'PyQt5.QtPositioning', 'PyQt5.QtLocation', 'PyQt5.QtNfc', 'PyQt5.QtRemoteObjects', 'PyQt5.QtPurchasing', 'tkinter', 'unittest', 'pydoc', 'xmlrpc', 'sqlite3', 'http.server', 'email'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QuickInput',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QuickInput',
)
