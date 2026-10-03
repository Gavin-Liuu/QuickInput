@echo off
cd /d "%~dp0"
echo Building QuickInput Portable Distribution...
python build_portable.py
pause
