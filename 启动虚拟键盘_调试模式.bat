@echo off
cd /d "%~dp0"

echo ==============================================
echo   QuickInput Floating Keyboard - Debug Mode
echo ==============================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python main.py
    goto FINISH
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 main.py
    goto FINISH
)

echo [ERROR] Python not found in PATH.

:FINISH
echo.
echo Process ended. Press any key to exit...
pause >nul
