# -*- coding: utf-8 -*-
"""Build script for creating standalone lightweight portable distribution of QuickInput."""

import os
import sys
import shutil
import subprocess
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")

# Modules not needed by QuickInput desktop widgets
EXCLUDE_MODULES = [
    "PyQt5.QtQuick",
    "PyQt5.QtQml",
    "PyQt5.QtPdf",
    "PyQt5.QtPdfWidgets",
    "PyQt5.QtNetwork",
    "PyQt5.QtSql",
    "PyQt5.QtMultimedia",
    "PyQt5.QtMultimediaWidgets",
    "PyQt5.QtXml",
    "PyQt5.QtXmlPatterns",
    "PyQt5.QtTest",
    "PyQt5.QtDesigner",
    "PyQt5.QtOpenGL",
    "PyQt5.QtPrintSupport",
    "PyQt5.Qt3DCore",
    "PyQt5.Qt3DRender",
    "PyQt5.Qt3DInput",
    "PyQt5.Qt3DLogic",
    "PyQt5.Qt3DAnimation",
    "PyQt5.Qt3DExtras",
    "PyQt5.QtSensors",
    "PyQt5.QtSerialPort",
    "PyQt5.QtWebSockets",
    "PyQt5.QtBluetooth",
    "PyQt5.QtPositioning",
    "PyQt5.QtLocation",
    "PyQt5.QtNfc",
    "PyQt5.QtRemoteObjects",
    "PyQt5.QtPurchasing",
    "tkinter",
    "unittest",
    "pydoc",
    "xmlrpc",
    "sqlite3",
    "http.server",
    "email",
]


def build():
    print("[1/5] Cleaning previous build artifacts...")
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    clean_venv_py = os.path.join(BASE_DIR, ".venv_clean", "Scripts", "python.exe")
    target_py = clean_venv_py if os.path.exists(clean_venv_py) else sys.executable
    print(f"[2/5] Running PyInstaller with modular exclusions using: {target_py}")

    cmd = [
        target_py,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "QuickInput",
        "--add-data",
        f"packs{os.pathsep}packs",
    ]
    for mod in EXCLUDE_MODULES:
        cmd.extend(["--exclude-module", mod])

    cmd.append("main.py")

    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode != 0:
        print("[ERROR] PyInstaller build failed!")
        sys.exit(res.returncode)

    output_dir = os.path.join(DIST_DIR, "QuickInput")

    print("[3/5] Optimizing runtime package size (removing unused heavy binaries)...")
    # Giant unused Mesa software renderer (21MB) & unused sub-modules
    unused_binaries = [
        "opengl32sw.dll",
        "Qt5Pdf_conda.dll",
        "Qt5PdfWidgets_conda.dll",
        "Qt5Quick_conda.dll",
        "Qt5Qml_conda.dll",
        "Qt5QmlModels_conda.dll",
        "Qt5VirtualKeyboard_conda.dll",
    ]
    for root, dirs, files in os.walk(output_dir):
        for f in files:
            # Remove redundant dlls
            if f in unused_binaries:
                fp = os.path.join(root, f)
                try:
                    os.remove(fp)
                    print(f"  Removed unused binary: {f}")
                except Exception:
                    pass
            # Remove all translation .qm files except zh_CN
            elif f.endswith(".qm") and not f.startswith("qt_zh_CN"):
                fp = os.path.join(root, f)
                try:
                    os.remove(fp)
                except Exception:
                    pass

        # Prune unused platform plugins (keep only qwindows.dll)
        if os.path.basename(root) == "platforms":
            for pfile in files:
                if pfile != "qwindows.dll" and pfile.endswith(".dll"):
                    try:
                        os.remove(os.path.join(root, pfile))
                        print(f"  Removed unused platform plugin: {pfile}")
                    except Exception:
                        pass
        elif os.path.basename(root) == "imageformats":
            for ifile in files:
                if ifile.startswith(("qwebp", "qtiff", "qwbmp", "qtga")):
                    try:
                        os.remove(os.path.join(root, ifile))
                        print(f"  Removed unused image format plugin: {ifile}")
                    except Exception:
                        pass

    print(f"[4/5] Copying packs and release helpers to {output_dir}...")
    dest_packs = os.path.join(output_dir, "packs")
    if not os.path.exists(dest_packs):
        shutil.copytree(os.path.join(BASE_DIR, "packs"), dest_packs, dirs_exist_ok=True)

    # Create README.txt in portable release folder
    readme_txt = """===============================================================
  通用快捷输入工作台 (QuickInput) - 免安装便携版
===============================================================

【快速开始】
1. 双击运行 `QuickInput.exe` 即可启动悬浮动作面板。
2. 默认置顶悬浮在屏幕上，支持鼠标按住标题栏任意拖动。
3. 点击顶部下拉菜单可一键在【Word 常用排版】、【图片标注】、【客服话术】、【程序员】等场景之间切换。
4. 点击齿轮图标打开设置中心，可按布局添加按钮、录制按键/组合键、设置透明度、切换中英文语言和绑定目标软件。
5. 点击原生窗口关闭按钮 `×` 会最小化隐藏到托盘；真正退出请右键点击右下角系统托盘图标，选择“退出程序”。

【常用快捷键】
- Alt + Q : 全局显示 / 隐藏悬浮工作台
- Esc     : 紧急停止当前正在执行的宏

【排查与调试】
若遇到闪退或异常，可双击 `QuickInput_Debug.bat` 查看详细运行日志。

【关于安全软件提示】
本程序使用 Windows 官方提供的 SendInput API 模拟键盘输入，不含任何木马或恶意后门。
若 Windows Defender 或安全卫士误报，请添加信任即可。
"""
    with open(os.path.join(output_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme_txt)

    # Create debug launcher
    debug_bat = """@echo off
cd /d "%~dp0"
echo [QuickInput Debug Mode] Launching QuickInput.exe with console...
QuickInput.exe
pause
"""
    with open(os.path.join(output_dir, "QuickInput_Debug.bat"), "w", encoding="utf-8") as f:
        f.write(debug_bat)

    # Create ZIP archive with maximum DEFLATED compression
    zip_path = os.path.join(DIST_DIR, "QuickInput_v1.0.0_Windows_x64.zip")
    print(f"[5/5] Compressing portable distribution to {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, DIST_DIR)
                zipf.write(full_path, rel_path)

    folder_size_mb = sum(
        os.path.getsize(os.path.join(r, f)) for r, d, fs in os.walk(output_dir) for f in fs
    ) / (1024 * 1024)
    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)

    print("\n" + "=" * 60)
    print("  [SUCCESS] Portable release build completed!")
    print(f"  Uncompressed Directory Size: {folder_size_mb:.2f} MB")
    print(f"  Compressed ZIP Package Size:  {zip_size_mb:.2f} MB")
    print(f"  ZIP Output: {zip_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    build()
