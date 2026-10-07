@echo off
cd /d "%~dp0"

:: Check standalone portable executable first
if exist "%~dp0dist\QuickInput\QuickInput.exe" (
    start "" "%~dp0dist\QuickInput\QuickInput.exe"
    exit /b 0
)

:: Check pythonw in PATH
where pythonw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" pythonw main.py
    exit /b 0
)

:: Check standard Windows pyw launcher
where pyw >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" pyw main.py
    exit /b 0
)

:: Fallback to python in PATH
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" python main.py
    exit /b 0
)

:: Fallback to py launcher
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" py main.py
    exit /b 0
)

echo [ERROR] Python was not found in PATH.
echo Please install Python 3.10+ or run build.bat to generate the portable executable.
pause
