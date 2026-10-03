# -*- coding: utf-8 -*-
"""Build script for creating standalone portable distribution of QuickInput."""

import os
import sys
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")


def build():
    print("[1/4] Cleaning previous build artifacts...")
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR, ignore_errors=True)
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    print("[2/4] Running PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "QuickInput",
        "--add-data",
        f"packs{os.pathsep}packs",
        "main.py",
    ]
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode != 0:
        print("[ERROR] PyInstaller build failed!")
        sys.exit(res.returncode)

    output_dir = os.path.join(DIST_DIR, "QuickInput")
    print(f"[3/4] Copying packs and resources to {output_dir}...")
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
3. 点击顶部下拉菜单可一键在【象棋】、【图片标注】、【客服话术】、【程序员】等场景之间切换。
4. 点击齿轮图标 `⚙` 打开设置中心，可按布局添加按钮、编辑宏、录制按键、设置透明度和绑定目标软件。
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

    print("[4/4] Portable build successfully completed!")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    build()
