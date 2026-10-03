@echo off
cd /d "%~dp0"

echo ==============================================
echo   Chess Floating Keyboard - Debug Mode
echo ==============================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python floating_keyboard.py
    goto FINISH
)

if exist "E:\apps\Anaconda3\python.exe" (
    "E:\apps\Anaconda3\python.exe" floating_keyboard.py
    goto FINISH
)

echo [ERROR] Python not found.

:FINISH
echo.
echo Process ended. Press any key to exit...
pause >nul
