import os, sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QFileDialog,
    QTabWidget,
    QSystemTrayIcon,
    QMenu,
)
from threading import Thread
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
        self.config_editor = QTextEdit()
        try:
            with open(self.core.config_path, "r") as f:
                self.config_editor.setPlainText(f.read())
        except Exception:
            self.config_editor.setPlainText("# Unable to load config.yaml")
        # --- Monitor Tab ---
        self.status_label = QLabel("Status: Idle")
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.reload_btn = QPushButton("Reload")
        self.viewlog_btn = QPushButton("View Log")
        self.settings_btn = QPushButton("Settings")

        vbox = QVBoxLayout()
        for w in [
            self.status_label,
            self.text_area,
            self.start_btn,
            self.stop_btn,
            self.reload_btn,
            self.viewlog_btn,
            self.settings_btn,
        ]:
            vbox.addWidget(w)
        self.monitor_tab.setLayout(vbox)

        # --- Dashboard Tab ---
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.update_btn = QPushButton("Check for Update")
        dash_layout = QVBoxLayout()
        dash_layout.addWidget(self.canvas)
        dash_layout.addWidget(self.update_btn)
        self.dashboard_tab.setLayout(dash_layout)

        self.timestamps = []
        self.statuses = []

        # --- Main Layout ---
        self.setCentralWidget(self.tabs)
        self.core = WatchdogCore()
        self.thread = None

        self.tray = QSystemTrayIcon(
            QIcon(icon_path)
            if os.path.exists(icon_path)
            else self.style().standardIcon(
                self.style().StandardPixmap.SP_MessageBoxInformation
            )
        )
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
        self.reload_btn.clicked.connect(self.reload_config)
        self.viewlog_btn.clicked.connect(self.view_log)
        self.settings_btn.clicked.connect(self.open_settings)

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
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QFormLayout(dialog)

        url_input = QLineEdit(settings.get("target_url", ""))
        interval_input = QLineEdit(str(settings.get("check_interval", 30)))
        retries_input = QLineEdit(str(settings.get("retries", 3)))

        layout.addRow("Target URL", url_input)
        layout.addRow("Check Interval (s)", interval_input)
        layout.addRow("Retries", retries_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addRow(buttons)

        def save_settings():
            new_settings = {
                "target_url": url_input.text().strip(),
                "check_interval": int(interval_input.text().strip() or 30),
                "retries": int(retries_input.text().strip() or 3),
            }
            self.core.save_settings(new_settings)
            self.log_message("💾 Settings saved.")
            dialog.accept()

        buttons.accepted.connect(save_settings)
        buttons.rejected.connect(dialog.reject)
        dialog.exec()

    def reload_config(self):
        self.core.settings = self.core.load_settings()
        self.log_message("🔁 Settings reloaded.")

    def save_config(self):
        self.open_settings()

    def closeEvent(self, event):
        try:
            self.core.stop()
        except Exception:
            pass
        QApplication.quit()
        event.accept()

    def view_log(self):
        import os, subprocess

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
