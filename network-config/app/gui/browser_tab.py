from __future__ import annotations

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QComboBox, QLabel, QProgressBar,
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
    _WEBENGINE_AVAILABLE = True
except ImportError:
    _WEBENGINE_AVAILABLE = False

import core.config_manager as cfg


_KNOWN_DEVICES = [
    ("Asus RT-BE50",        lambda: f"http://{cfg.get('devices.asus_rt_be50.ip', '192.168.50.1')}"),
    ("Home Assistant",      lambda: f"http://{cfg.get('devices.homeassistant.ip', '192.168.50.10')}:8123"),
    ("Sonoff Dongle Max",   lambda: f"http://{cfg.get('devices.sonoff_zigbee.ip', '192.168.50.5')}"),
    ("Vodafone CGA4233VDF", lambda: "http://192.168.0.1"),
    ("Movistar HGU",        lambda: "http://192.168.1.1"),
]


class BrowserTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # --- Barra de navegación ---
        nav_bar = QHBoxLayout()

        self._device_combo = QComboBox()
        for name, _ in _KNOWN_DEVICES:
            self._device_combo.addItem(name)
        self._device_combo.currentIndexChanged.connect(self._load_from_combo)
        nav_bar.addWidget(self._device_combo)

        self._url_bar = QLineEdit()
        self._url_bar.setPlaceholderText("http://192.168.50.1")
        self._url_bar.returnPressed.connect(self._navigate_to_url_bar)
        nav_bar.addWidget(self._url_bar, stretch=1)

        btn_go = QPushButton("Ir")
        btn_go.setFixedWidth(40)
        btn_go.clicked.connect(self._navigate_to_url_bar)
        nav_bar.addWidget(btn_go)

        btn_back = QPushButton("◀")
        btn_back.setFixedWidth(32)
        nav_bar.addWidget(btn_back)

        btn_forward = QPushButton("▶")
        btn_forward.setFixedWidth(32)
        nav_bar.addWidget(btn_forward)

        btn_reload = QPushButton("↻")
        btn_reload.setFixedWidth(32)
        nav_bar.addWidget(btn_reload)

        layout.addLayout(nav_bar)

        # --- Vista web o aviso ---
        if _WEBENGINE_AVAILABLE:
            self._view = QWebEngineView()
            self._view.settings().setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
            )
            self._progress = QProgressBar()
            self._progress.setMaximumHeight(4)
            self._progress.setTextVisible(False)
            self._progress.setStyleSheet("QProgressBar { border: none; } QProgressBar::chunk { background: #4a9eff; }")

            self._view.urlChanged.connect(lambda url: self._url_bar.setText(url.toString()))
            self._view.loadProgress.connect(self._progress.setValue)
            self._view.loadFinished.connect(lambda _: self._progress.setValue(0))

            btn_back.clicked.connect(self._view.back)
            btn_forward.clicked.connect(self._view.forward)
            btn_reload.clicked.connect(self._view.reload)

            layout.addWidget(self._progress)
            layout.addWidget(self._view)

            # Cargar el primer dispositivo al arrancar
            self._load_from_combo(0)
        else:
            btn_back.setEnabled(False)
            btn_forward.setEnabled(False)
            btn_reload.setEnabled(False)

            warn = QLabel(
                "⚠️  PyQt6-WebEngine no está instalado.\n\n"
                "Para activar el navegador embebido, ejecuta en la terminal:\n"
                "    pip install PyQt6-WebEngine\n\n"
                "O vuelve a ejecutar install.bat para instalar todas las dependencias."
            )
            warn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            warn.setStyleSheet("color: #f9e2af; font-size: 13px;")
            layout.addWidget(warn)

    def _load_from_combo(self, index: int) -> None:
        if not _WEBENGINE_AVAILABLE:
            return
        _, url_fn = _KNOWN_DEVICES[index]
        url = url_fn()
        self._url_bar.setText(url)
        self._view.load(QUrl(url))

    def _navigate_to_url_bar(self) -> None:
        if not _WEBENGINE_AVAILABLE:
            return
        url = self._url_bar.text().strip()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        self._view.load(QUrl(url))

    def navigate_to(self, url: str) -> None:
        """Navega a una URL concreta y selecciona el dispositivo correspondiente."""
        if not _WEBENGINE_AVAILABLE:
            return
        self._url_bar.setText(url)
        self._view.load(QUrl(url))
