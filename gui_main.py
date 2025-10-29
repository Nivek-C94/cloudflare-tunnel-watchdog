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
)
from threading import Thread
from watchdog_core import WatchdogCore


class WatchdogGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cloudflare Tunnel Watchdog")
        # Set window icon
        if getattr(sys, "frozen", False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        icon_path = os.path.join(base_path, "cloudflare_watchdog_logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.status_label = QLabel("Status: Idle")
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)

        self.start_btn = QPushButton("Start Watchdog")
        self.stop_btn = QPushButton("Stop Watchdog")
        self.load_cfg_btn = QPushButton("Edit Config")

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.text_area)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.load_cfg_btn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.core = WatchdogCore()
        self.thread = None

        self.start_btn.clicked.connect(self.start_watchdog)
        self.stop_btn.clicked.connect(self.stop_watchdog)
        self.load_cfg_btn.clicked.connect(self.edit_config)

    def start_watchdog(self):
        if not self.thread or not self.thread.is_alive():
            self.thread = Thread(target=self.core.start, args=(self.log_message,))
            self.thread.daemon = True
            self.thread.start()
            self.status_label.setText("Status: Running")
            self.log_message("▶️ Watchdog started.")

    def stop_watchdog(self):
        self.core.stop()
        self.status_label.setText("Status: Stopped")
        self.log_message("⏹️ Watchdog stopped.")

    def log_message(self, msg):
        self.text_area.append(msg)
        self.text_area.ensureCursorVisible()

    def edit_config(self):
        path = self.core.config_path
        QFileDialog.getOpenFileName(
            self, "Open Config File", path, "YAML Files (*.yaml *.yml)"
        )
        self.log_message("📝 Opened config for editing.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = WatchdogGUI()
    gui.show()
    sys.exit(app.exec())
