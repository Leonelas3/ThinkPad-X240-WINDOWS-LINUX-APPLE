from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QPushButton,
    QStatusBar, QLabel, QApplication,
)
from PyQt6.QtGui import QAction

import core.db as db
from core.scanner import NetworkScanner
from gui.styles import DARK_STYLESHEET
from gui.devices_tab import DevicesTab, ScanWorker
from gui.config_tab import ConfigTab
from gui.log_tab import LogTab
from gui.browser_tab import BrowserTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión Red Doméstica — 192.168.50.0/24")
        self.resize(1100, 700)
        self._center_window()
        self.setStyleSheet(DARK_STYLESHEET)

        self._scanner = NetworkScanner()
        self._scan_thread: QThread | None = None

        self._build_toolbar()
        self._build_tabs()
        self._build_status_bar()

        self.update_status("Aplicación iniciada")
        self._auto_scan()

    def _center_window(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(x, y)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        scan_action = QAction("🔍 Escanear red", self)
        scan_action.setToolTip("Escanea toda la subred 192.168.50.0/24")
        scan_action.triggered.connect(self._trigger_scan)
        toolbar.addAction(scan_action)

        toolbar.addSeparator()

        subnet_label = QLabel("  Subred: 192.168.50.0/24  ")
        subnet_label.setStyleSheet("color: #4a9eff; font-weight: bold; background: transparent;")
        toolbar.addWidget(subnet_label)

    def _build_tabs(self) -> None:
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        self._devices_tab = DevicesTab(self)
        self._config_tab = ConfigTab(self)
        self._log_tab = LogTab(self)
        self._browser_tab = BrowserTab()

        self._tabs.addTab(self._devices_tab, "🔍 Dispositivos")
        self._tabs.addTab(self._config_tab, "⚙️ Configuración")
        self._tabs.addTab(self._log_tab, "📋 Historial")
        self._tabs.addTab(self._browser_tab, "🌐 Interfaz Web")

        # Recarga el log al entrar al tab
        self._tabs.currentChanged.connect(self._on_tab_changed)

    def _build_status_bar(self) -> None:
        self._status_label = QLabel("—")
        self.statusBar().addWidget(self._status_label)

    def _on_tab_changed(self, index: int) -> None:
        if index == 2:
            self._log_tab.load_data()

    def update_status(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._status_label.setText(f"[{ts}] {message}")

    def log_action(
        self,
        device: str,
        action: str,
        old_value: str,
        new_value: str,
        status: str = "ok",
        reversible: bool = False,
        revert_data: str | None = None,
    ) -> None:
        db.log_change(device, action, old_value, new_value, reversible, revert_data, status)
        self.update_status(f"{device}: {action}")

    def open_config_for_device(self, device_index: int) -> None:
        self._tabs.setCurrentIndex(1)
        self._config_tab.show_device(device_index)

    def _trigger_scan(self) -> None:
        self._tabs.setCurrentIndex(0)
        self._devices_tab.start_scan()

    def _auto_scan(self) -> None:
        # Escaneo automático al arrancar en background
        self._devices_tab.start_scan()
