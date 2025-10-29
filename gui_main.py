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
        self.config_tab = QWidget()
        self.dashboard_tab = QWidget()

        self.tabs.addTab(self.monitor_tab, "Monitor")
        self.tabs.addTab(self.config_tab, "Config")
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
        self.reload_btn = QPushButton("Reload Config")
        self.viewlog_btn = QPushButton("View Log")

        vbox = QVBoxLayout()
        for w in [
            self.status_label,
            self.text_area,
            self.start_btn,
            self.stop_btn,
            self.reload_btn,
            self.viewlog_btn,
        ]:
            vbox.addWidget(w)
        self.monitor_tab.setLayout(vbox)

        # --- Config Tab ---
        self.config_editor = QTextEdit()
        self.save_config_btn = QPushButton("Save Config")
        config_layout = QVBoxLayout()
        config_layout.addWidget(self.config_editor)
        config_layout.addWidget(self.save_config_btn)
        self.config_tab.setLayout(config_layout)

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
        tray_menu.addAction("Restore", self.showNormal)
        tray_menu.addAction("Exit", QApplication.quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.show()

        # --- Bind Buttons ---
        self.start_btn.clicked.connect(self.start_watchdog)
        self.stop_btn.clicked.connect(self.stop_watchdog)
        self.reload_btn.clicked.connect(self.reload_config)
        self.viewlog_btn.clicked.connect(self.view_log)
        self.save_config_btn.clicked.connect(self.save_config)

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

    def reload_config(self):
        self.core.load_config()
        self.log_message("🔁 Configuration reloaded.")

    def log_message(self, msg):
        self.text_area.append(msg)
        lines = self.text_area.toPlainText().splitlines()
        if len(lines) > 500:
            self.text_area.setPlainText("\n".join(lines[-500:]))
        self.text_area.ensureCursorVisible()

    def view_log(self):
        import subprocess

        log_path = os.path.join(os.path.dirname(__file__), "watchdog.log")
        if os.path.exists(log_path):
            os.startfile(log_path)
        else:
            self.log_message("⚠️ Log file not found.")

    def save_config(self):
        with open(self.core.config_path, "w") as f:
            f.write(self.config_editor.toPlainText())
        self.log_message("💾 Config saved.")

    def closeEvent(self, event):
        try:
            self.core.stop()
        except Exception:
            pass
        QApplication.quit()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = WatchdogGUI()
    gui.show()
    sys.exit(app.exec())
