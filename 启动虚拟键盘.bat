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
    start "" pythonw floating_keyboard.py
    exit /b 0
)

:: Check Anaconda3 pythonw directly
if exist "E:\apps\Anaconda3\pythonw.exe" (
    start "" "E:\apps\Anaconda3\pythonw.exe" floating_keyboard.py
    exit /b 0
)

:: Fallback to python in PATH
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" python floating_keyboard.py
    exit /b 0
)

:: Fallback to Anaconda3 python directly
if exist "E:\apps\Anaconda3\python.exe" (
    start "" "E:\apps\Anaconda3\python.exe" floating_keyboard.py
    exit /b 0
)

echo [ERROR] Python was not found in PATH or at E:\apps\Anaconda3\python.exe
pause
