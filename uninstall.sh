#!/bin/bash
# 🧹 Cloudflare Tunnel Watchdog Uninstaller
# This script disables and removes the systemd service, logs, and temporary files.

SERVICE_NAME="cloudflare-watchdog.service"
INSTALL_PATH="/etc/systemd/system/${SERVICE_NAME}"
PROJECT_PATH="$HOME/cloudflare-tunnel-watchdog"

# Confirm action
echo "⚠️  This will disable and remove the Cloudflare Tunnel Watchdog service."
read -p "Are you sure you want to continue? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "❌ Uninstall cancelled."
    exit 1
fi

# Stop and disable service
sudo systemctl stop $SERVICE_NAME 2>/dev/null
sudo systemctl disable $SERVICE_NAME 2>/dev/null

# Remove systemd service file
if [ -f "$INSTALL_PATH" ]; then
    sudo rm "$INSTALL_PATH"
    echo "🗑️  Removed service file: $INSTALL_PATH"
else
    echo "⚠️  Service file not found (already removed)."
fi

# Reload systemd daemon
sudo systemctl daemon-reload

# Optionally remove logs
LOG_FILE="$PROJECT_PATH/watchdog.log"
if [ -f "$LOG_FILE" ]; then
    rm "$LOG_FILE"
    echo "🧾 Removed log file: $LOG_FILE"
fi

# Optionally remove project files
read -p "Do you want to remove the project folder ($PROJECT_PATH)? (y/N): " delete_project
if [[ "$delete_project" =~ ^[Yy]$ ]]; then
    rm -rf "$PROJECT_PATH"
    echo "📦 Project folder removed."
else
    echo "✅ Project folder kept intact."
fi

echo "✨ Cloudflare Tunnel Watchdog fully uninstalled."
exit 0