#!/bin/bash
# Build script for packaging the Cloudflare Tunnel Watchdog GUI into a standalone executable.

set -e

APP_NAME="CloudflareTunnelWatchdog"
ENTRY_POINT="gui_main.py"
OUTPUT_DIR="dist"

# Ensure dependencies
python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller PyQt6 pyyaml requests

# Clean previous builds
rm -rf build $OUTPUT_DIR *.spec

# Package with PyInstaller
pyinstaller --onefile --noconsole --name "$APP_NAME" "$ENTRY_POINT"

# Move output to dist/
echo "✅ Build complete. Executable located at: $OUTPUT_DIR/$APP_NAME"

# Optional: Linux users can make it executable
chmod +x $OUTPUT_DIR/$APP_NAME