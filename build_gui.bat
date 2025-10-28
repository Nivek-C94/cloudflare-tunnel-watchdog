@echo off
REM Build script for packaging the Cloudflare Tunnel Watchdog GUI into a standalone Windows executable.

set APP_NAME=CloudflareTunnelWatchdog
set ENTRY_POINT=gui_main.py
set OUTPUT_DIR=dist

REM Ensure dependencies
python -m pip install --upgrade pip
python -m pip install pyinstaller PyQt6 pyyaml requests

REM Clean previous builds
if exist build rmdir /s /q build
if exist %OUTPUT_DIR% rmdir /s /q %OUTPUT_DIR%
del /q *.spec 2>nul

REM Package with PyInstaller
pyinstaller --onefile --noconsole --name %APP_NAME% %ENTRY_POINT%

if %ERRORLEVEL% neq 0 (
    echo ❌ Build failed.
    exit /b %ERRORLEVEL%
)

echo ✅ Build complete. Executable located at %OUTPUT_DIR%\%APP_NAME%.exe
pause