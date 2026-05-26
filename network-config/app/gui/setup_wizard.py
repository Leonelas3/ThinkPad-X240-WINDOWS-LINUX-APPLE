from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QFormLayout,
    QLabel, QLineEdit, QGroupBox,
)

import core.config_manager as cfg


class _IntroPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Bienvenido al Asistente de Configuración")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Este asistente te guiará para introducir las credenciales\n"
            "de cada dispositivo de la red.\n\n"
            "Las credenciales se guardan SOLO en config.json en tu PC.\n"
            "Nunca se suben a GitHub ni a ningún servicio externo.\n\n"
            "Pulsa Siguiente para continuar."
        ))


class _AsusPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Asus RT-BE50 — Router principal")
        self.setSubTitle("Usuario y contraseña de la interfaz web del router (192.168.50.1)")

        form = QFormLayout(self)

        self._ip = QLineEdit(cfg.get("devices.asus_rt_be50.ip", "192.168.50.1"))
        self._user = QLineEdit(cfg.get("devices.asus_rt_be50.username", "admin"))
        self._pass = QLineEdit(cfg.get("devices.asus_rt_be50.password", ""))
        self._pass.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("IP del router:", self._ip)
        form.addRow("Usuario:", self._user)
        form.addRow("Contraseña:", self._pass)

        note = QLabel("💡 La contraseña es la misma que usas para entrar a http://192.168.50.1")
        note.setStyleSheet("color: #4a9eff; font-size: 11px;")
        form.addRow("", note)

    def validatePage(self) -> bool:
        cfg.set_value("devices.asus_rt_be50.ip", self._ip.text().strip())
        cfg.set_value("devices.asus_rt_be50.username", self._user.text().strip())
        cfg.set_value("devices.asus_rt_be50.password", self._pass.text())
        return True


class _HAPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Home Assistant — ThinkPad X250")
        self.setSubTitle("Token de larga duración para acceder al API de Home Assistant")

        layout = QVBoxLayout(self)

        how_to = QGroupBox("Cómo obtener el token")
        how_layout = QVBoxLayout(how_to)
        how_layout.addWidget(QLabel(
            "1. Abre Home Assistant en http://192.168.50.10:8123\n"
            "2. Clic en tu perfil (esquina inferior izquierda)\n"
            "3. Baja hasta 'Tokens de larga duración'\n"
            "4. Clic en 'Crear token' → ponle nombre → copia el token"
        ))
        layout.addWidget(how_to)

        form = QFormLayout()
        self._ip = QLineEdit(cfg.get("devices.homeassistant.ip", "192.168.50.10"))
        self._token = QLineEdit(cfg.get("devices.homeassistant.token", ""))
        self._token.setEchoMode(QLineEdit.EchoMode.Password)
        self._token.setPlaceholderText("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")

        form.addRow("IP de Home Assistant:", self._ip)
        form.addRow("Token:", self._token)
        layout.addLayout(form)

    def validatePage(self) -> bool:
        cfg.set_value("devices.homeassistant.ip", self._ip.text().strip())
        cfg.set_value("devices.homeassistant.token", self._token.text().strip())
        return True


class _SonoffPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Sonoff Dongle Max — Coordinador Zigbee")
        self.setSubTitle("El Sonoff se conecta por LAN. No necesita contraseña, solo su IP.")

        form = QFormLayout(self)

        self._ip = QLineEdit(cfg.get("devices.sonoff_zigbee.ip", "192.168.50.5"))
        self._port = QLineEdit(str(cfg.get("devices.sonoff_zigbee.zha_port", 6638)))

        form.addRow("IP del Sonoff:", self._ip)
        form.addRow("Puerto ZHA (TCP):", self._port)

        note = QLabel(
            "💡 Puedes confirmar la IP abriendo http://192.168.50.5 en el navegador.\n"
            "El puerto 6638 es el estándar del firmware del Sonoff Dongle Max."
        )
        note.setStyleSheet("color: #4a9eff; font-size: 11px;")
        note.setWordWrap(True)
        form.addRow("", note)

    def validatePage(self) -> bool:
        cfg.set_value("devices.sonoff_zigbee.ip", self._ip.text().strip())
        try:
            cfg.set_value("devices.sonoff_zigbee.zha_port", int(self._port.text().strip()))
        except ValueError:
            pass
        return True


class _DuckDNSPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("DuckDNS — Acceso externo a Home Assistant")
        self.setSubTitle("Dominio y token para que Google Home y las apps externas lleguen a tu HA")

        form = QFormLayout(self)

        self._domain = QLineEdit(cfg.get("duckdns.domain", "leonelastres.duckdns.org"))
        self._token = QLineEdit(cfg.get("duckdns.token", ""))
        self._token.setEchoMode(QLineEdit.EchoMode.Password)
        self._token.setPlaceholderText("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")

        form.addRow("Dominio DuckDNS:", self._domain)
        form.addRow("Token DuckDNS:", self._token)

        note = QLabel("💡 El token lo encuentras en https://www.duckdns.org cuando inicias sesión.")
        note.setStyleSheet("color: #4a9eff; font-size: 11px;")
        note.setWordWrap(True)
        form.addRow("", note)

    def validatePage(self) -> bool:
        cfg.set_value("duckdns.domain", self._domain.text().strip())
        cfg.set_value("duckdns.token", self._token.text().strip())
        return True


class _FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Configuración guardada")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "✅ Las credenciales han sido guardadas en config.json.\n\n"
            "Puedes editarlas en cualquier momento desde:\n"
            "  → Pestaña ⚙️ Configuración → panel de cada dispositivo\n\n"
            "La aplicación ya está lista para conectarse a tu red."
        ))


class SetupWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración inicial — Red Doméstica")
        self.resize(560, 420)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        self.addPage(_IntroPage())
        self.addPage(_AsusPage())
        self.addPage(_HAPage())
        self.addPage(_SonoffPage())
        self.addPage(_DuckDNSPage())
        self.addPage(_FinishPage())

        self.finished.connect(lambda: cfg.save())
