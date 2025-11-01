import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QTabWidget,
    QSystemTrayIcon,
    QSpinBox,
    QMenu,
)
from watchdog_core import WatchdogCore


class WatchdogGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cloudflare Tunnel Watchdog v2.0")

        # Load icon
        base_path = (
            os.path.dirname(sys.executable)
            if getattr(sys, "frozen", False)
            else os.path.dirname(__file__)
        )
        icon_path = os.path.join(base_path, "cloudflare_watchdog_logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.monitor_tab = QWidget()
        self.dashboard_tab = QWidget()
        self.tabs.addTab(self.monitor_tab, "Monitor")
        self.tabs.addTab(self.dashboard_tab, "Dashboard")

        # --- Monitor Tab Layout ---
        self.status_label = QLabel("Status: Idle")
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.viewlog_btn = QPushButton("View Log")
        self.settings_btn = QPushButton("Settings")

        monitor_layout = QVBoxLayout()
        monitor_layout.addWidget(self.status_label)
        monitor_layout.addWidget(self.text_area)

        button_row = QHBoxLayout()
        button_row.addWidget(self.start_btn)
        button_row.addWidget(self.stop_btn)
        button_row.addWidget(self.viewlog_btn)
        button_row.addWidget(self.settings_btn)

        monitor_layout.addLayout(button_row)
        self.monitor_tab.setLayout(monitor_layout)

        # --- Dashboard Tab Layout ---
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)

        dash_layout = QVBoxLayout()
        dash_layout.addWidget(self.canvas)

        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        dash_layout.addLayout(button_layout)

        self.dashboard_tab.setLayout(dash_layout)

        # --- Final Assembly ---
        self.setCentralWidget(self.tabs)
        self.core = WatchdogCore()
        self.thread = None

        # --- System Tray Icon with Fallback ---
        icon_path = os.path.join(base_path, "cloudflare_watchdog_logo.png")
        if not os.path.exists(icon_path):
            tray_icon = QSystemTrayIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
            )
            self.tray = tray_icon
            print("⚠️ App logo not found, using default tray icon.")
        else:
            tray_icon = QSystemTrayIcon(QIcon(icon_path))
            self.tray = tray_icon

        tray_menu = QMenu()
        tray_menu.addAction("Start", self.start_watchdog)
        tray_menu.addAction("Stop", self.stop_watchdog)
        tray_menu.addAction("Settings", self.open_settings)
        tray_menu.addAction("View Log", self.view_log)
        tray_menu.addAction("Restore", self.showNormal)
        tray_menu.addAction("Exit", QApplication.quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.show()

        # --- Bind Buttons ---
        self.start_btn.clicked.connect(self.start_watchdog)
        self.stop_btn.clicked.connect(self.stop_watchdog)
        self.viewlog_btn.clicked.connect(self.view_log)
        self.settings_btn.clicked.connect(self.open_settings)

    def log_message(self, msg: str):
        self.text_area.append(msg)
        self.text_area.ensureCursorVisible()
        self.tray.setToolTip(f"Cloudflare Watchdog – {msg[:60]}")

    def start_watchdog(self):
        if not self.thread or not self.thread.is_alive():
            from threading import Thread

            self.thread = Thread(target=self.core.start, args=(self.log_message,))
            self.thread.daemon = True
            self.thread.start()
            self.status_label.setText("Status: Running 🟢")
            self.tray.setToolTip("Cloudflare Watchdog - Online 🟢")
            self.log_message("▶️ Watchdog started.")

    def stop_watchdog(self):
        self.core.stop()
        self.status_label.setText("Status: Stopped 🔴")
        self.tray.setToolTip("Cloudflare Watchdog - Offline 🔴")
        self.log_message("⏹️ Watchdog stopped.")

    def open_settings(self):
        settings = self.core.settings
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QFormLayout(dialog)

        # Basic fields
        url_input = QLineEdit(settings.get("target_url", ""))
        interval_input = QSpinBox()
        interval_input.setValue(settings.get("check_interval", 30))

        layout.addRow("Target URL", url_input)
        layout.addRow("Check Interval (s)", interval_input)

        # Recovery command sections
        # Recovery command sections (single-line with horizontal scroll)
        site_down_input = QTextEdit()
        site_down_input.setPlainText("\n".join(settings.get("on_site_fail", [])))
        site_down_input.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        site_down_input.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        site_down_input.setFixedHeight(60)

        wifi_down_input = QTextEdit()
        wifi_down_input.setPlainText("\n".join(settings.get("on_wifi_fail", [])))
        wifi_down_input.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        wifi_down_input.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        wifi_down_input.setFixedHeight(60)

        recovery_input = QTextEdit()
        recovery_input.setPlainText("\n".join(settings.get("on_recovery", [])))
        recovery_input.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        recovery_input.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        recovery_input.setFixedHeight(60)

        layout.addRow("Site Down (one per line)", site_down_input)
        layout.addRow("Wi-Fi Down (one per line)", wifi_down_input)
        layout.addRow("On Recovery (one per line)", recovery_input)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(
            lambda: self.save_settings(
                dialog,
                url_input.text(),
                interval_input.value(),
                site_down_input.toPlainText(),
                wifi_down_input.toPlainText(),
                recovery_input.toPlainText(),
            )
        )
        layout.addWidget(save_btn)

        dialog.setLayout(layout)
        dialog.exec()

    def save_settings(
        self,
        dialog,
        target_url,
        interval,
        site_down_text,
        wifi_down_text,
        recovery_text,
    ):
        self.core.settings.update(
            {
                "target_url": target_url,
                "check_interval": interval,
                "on_site_fail": [
                    cmd.strip() for cmd in site_down_text.splitlines() if cmd.strip()
                ],
                "on_wifi_fail": [
                    cmd.strip() for cmd in wifi_down_text.splitlines() if cmd.strip()
                ],
                "on_recovery": [
                    cmd.strip() for cmd in recovery_text.splitlines() if cmd.strip()
                ],
            }
        )
        self.core.save_settings()
        self.core.reload_settings()
        self.log_message("💾 Settings updated and reloaded.")
        try:
            self.tray.showMessage(
                "✅ Settings Saved",
                "Your configuration changes were saved successfully.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        except Exception:
            pass
        dialog.accept()

    def view_log(self):
        import subprocess

        log_path = os.path.join(os.path.dirname(__file__), "watchdog.log")
        if os.path.exists(log_path):
            try:
                os.startfile(log_path)
            except Exception:
                subprocess.Popen(["xdg-open", log_path])
        else:
            self.log_message("⚠️ Log file not found.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = WatchdogGUI()
    gui.show()
    sys.exit(app.exec())
