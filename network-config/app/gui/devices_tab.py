from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QGridLayout, QProgressBar, QSizePolicy,
)

from core.scanner import NetworkScanner, DeviceInfo, KNOWN_DEVICES
from gui.styles import STATUS_INDICATOR

if TYPE_CHECKING:
    from gui.main_window import MainWindow


DEVICE_ICONS = {
    "router":        "🔀",
    "homeassistant": "🏠",
    "pc":            "💻",
    "zigbee":        "📡",
    "unknown":       "❓",
}


class ScanWorker(QObject):
    device_found = pyqtSignal(object)
    finished = pyqtSignal(list)
    progress = pyqtSignal(int, int)

    def __init__(self, scanner: NetworkScanner):
        super().__init__()
        self._scanner = scanner

    def run(self) -> None:
        self._scanner.device_found.connect(self.device_found)
        self._scanner.scan_finished.connect(self.finished)
        self._scanner.scan_progress.connect(self.progress)
        self._scanner.scan()


class DeviceCard(QFrame):
    configure_requested = pyqtSignal(str)

    def __init__(self, device_info: DeviceInfo | dict, parent=None):
        super().__init__(parent)
        self.setProperty("card", True)
        self.setFixedSize(240, 160)

        if isinstance(device_info, DeviceInfo):
            self._ip = device_info.ip
            self._name = device_info.device_name or device_info.hostname or device_info.ip
            self._type = device_info.device_type
            self._ports = device_info.open_ports
        else:
            self._ip = device_info["ip"]
            self._name = device_info["name"]
            self._type = device_info["type"]
            self._ports = []

        self._status = "unknown"
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        icon = QLabel(DEVICE_ICONS.get(self._type, "❓"))
        icon.setStyleSheet("font-size: 22px; background: transparent;")
        header.addWidget(icon)
        header.addStretch()

        self._indicator = QLabel()
        self._indicator.setStyleSheet(STATUS_INDICATOR["unknown"])
        self._indicator.setFixedSize(14, 14)
        header.addWidget(self._indicator)

        layout.addLayout(header)

        name_label = QLabel(self._name)
        name_label.setStyleSheet("font-weight: bold; font-size: 13px; background: transparent;")
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        self._ip_label = QLabel(self._ip)
        self._ip_label.setStyleSheet("color: #4a9eff; font-size: 12px; background: transparent;")
        layout.addWidget(self._ip_label)

        self._status_label = QLabel("Comprobando...")
        self._status_label.setStyleSheet("color: #f9e2af; font-size: 11px; background: transparent;")
        layout.addWidget(self._status_label)

        layout.addStretch()

        btn = QPushButton("Configurar")
        btn.setFixedHeight(28)
        btn.clicked.connect(lambda: self.configure_requested.emit(self._ip))
        layout.addWidget(btn)

    def set_status(self, status: str, ports: list[int] | None = None) -> None:
        self._status = status
        self._indicator.setStyleSheet(STATUS_INDICATOR.get(status, STATUS_INDICATOR["unknown"]))
        if status == "online":
            port_str = f"  Puertos: {', '.join(str(p) for p in ports)}" if ports else ""
            self._status_label.setText(f"En línea{port_str}")
            self._status_label.setStyleSheet("color: #a6e3a1; font-size: 11px; background: transparent;")
        elif status == "offline":
            self._status_label.setText("Fuera de línea")
            self._status_label.setStyleSheet("color: #f38ba8; font-size: 11px; background: transparent;")
        elif status == "checking":
            self._status_label.setText("Comprobando...")
            self._status_label.setStyleSheet("color: #f9e2af; font-size: 11px; background: transparent;")


class DevicesTab(QWidget):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self._main = main_window
        self._cards: dict[str, DeviceCard] = {}
        self._unknown_cards: dict[str, DeviceCard] = {}
        self._scan_thread: QThread | None = None
        self._scanner = NetworkScanner()
        self._build_ui()
        self._populate_known_devices()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        toolbar = QHBoxLayout()
        self._scan_btn = QPushButton("🔍 Escanear red")
        self._scan_btn.clicked.connect(self.start_scan)
        toolbar.addWidget(self._scan_btn)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setFixedHeight(18)
        self._progress.setTextVisible(True)
        toolbar.addWidget(self._progress, 1)

        toolbar.addStretch()
        root.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self._container_layout = QVBoxLayout(container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(16)

        known_label = QLabel("Dispositivos conocidos")
        known_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4a9eff; background: transparent;")
        self._container_layout.addWidget(known_label)

        self._known_grid = QGridLayout()
        self._known_grid.setSpacing(12)
        self._container_layout.addLayout(self._known_grid)

        self._unknown_section = QWidget()
        unknown_layout = QVBoxLayout(self._unknown_section)
        unknown_layout.setContentsMargins(0, 0, 0, 0)

        self._unknown_label = QLabel("Dispositivos no identificados")
        self._unknown_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #f9e2af; background: transparent;"
        )
        unknown_layout.addWidget(self._unknown_label)

        self._unknown_grid = QGridLayout()
        self._unknown_grid.setSpacing(12)
        unknown_layout.addLayout(self._unknown_grid)

        self._unknown_section.setVisible(False)
        self._container_layout.addWidget(self._unknown_section)
        self._container_layout.addStretch()

        scroll.setWidget(container)
        root.addWidget(scroll)

    def _populate_known_devices(self) -> None:
        known = [
            {"ip": "192.168.50.1",  "name": "Asus RT-BE50",         "type": "router"},
            {"ip": "192.168.50.10", "name": "ThinkPad X250 (HAOS)", "type": "homeassistant"},
            {"ip": "192.168.50.20", "name": "HP Pro Mini 400 G9",    "type": "pc"},
            {"ip": "192.168.50.5",  "name": "Sonoff Dongle Max",     "type": "zigbee"},
        ]
        for idx, dev in enumerate(known):
            card = DeviceCard(dev)
            card.configure_requested.connect(self._open_config_for_device)
            card.set_status("checking")
            self._cards[dev["ip"]] = card
            row, col = divmod(idx, 4)
            self._known_grid.addWidget(card, row, col)

    def start_scan(self) -> None:
        if self._scan_thread and self._scan_thread.isRunning():
            return

        for card in self._cards.values():
            card.set_status("checking")

        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._scan_btn.setEnabled(False)

        worker = ScanWorker(self._scanner)
        self._scan_thread = QThread()
        worker.moveToThread(self._scan_thread)

        self._scan_thread.started.connect(worker.run)
        worker.device_found.connect(self._on_device_found)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_scan_finished)
        worker.finished.connect(self._scan_thread.quit)
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)

        self._scan_thread.start()

    def _on_device_found(self, info: DeviceInfo) -> None:
        if info.ip in self._cards:
            self._cards[info.ip].set_status("online", info.open_ports)
        else:
            self._add_unknown_device(info)

    def _add_unknown_device(self, info: DeviceInfo) -> None:
        if info.ip in self._unknown_cards:
            return
        self._unknown_section.setVisible(True)
        card = DeviceCard(info)
        card.set_status("online", info.open_ports)
        self._unknown_cards[info.ip] = card
        count = len(self._unknown_cards) - 1
        row, col = divmod(count, 4)
        self._unknown_grid.addWidget(card, row, col)

    def _on_progress(self, done: int, total: int) -> None:
        self._progress.setMaximum(total)
        self._progress.setValue(done)
        self._progress.setFormat(f"Escaneando... {done}/{total}")

    def _on_scan_finished(self, results: list) -> None:
        self._progress.setVisible(False)
        self._scan_btn.setEnabled(True)

        found_ips = {r.ip for r in results}
        for ip, card in self._cards.items():
            if ip not in found_ips:
                card.set_status("offline")

        self._main.update_status(
            f"Escaneo completado: {len(results)} dispositivos encontrados"
        )

    def _open_config_for_device(self, ip: str) -> None:
        device_map = {
            "192.168.50.1":  0,
            "192.168.50.10": 1,
            "192.168.50.5":  2,
            "192.168.50.20": 3,
        }
        self._main.open_config_for_device(device_map.get(ip, 0))
