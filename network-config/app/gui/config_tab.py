from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QStackedWidget, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QSizePolicy, QFormLayout,
    QTextEdit,
)

import core.config_manager as cfg
from core.devices.asus_rt_be50 import AsusRT_BE50
from core.devices.homeassistant_api import HomeAssistantAPI
from core.devices.sonoff_zigbee import SonoffZigbee

if TYPE_CHECKING:
    from gui.main_window import MainWindow


def _confirm(parent: QWidget, title: str, message: str) -> bool:
    reply = QMessageBox.question(
        parent, title, message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


class _AsyncWorker(QObject):
    result = pyqtSignal(bool, str)

    def __init__(self, func, *args):
        super().__init__()
        self._func = func
        self._args = args

    def run(self) -> None:
        try:
            ok, msg = self._func(*self._args)
            self.result.emit(ok, str(msg))
        except Exception as e:
            self.result.emit(False, str(e))


class AsusPanel(QWidget):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self._main = main_window
        self._asus: AsusRT_BE50 | None = None
        self._build_ui()

    def _get_asus(self) -> AsusRT_BE50:
        if self._asus is None:
            self._asus = AsusRT_BE50(
                ip=cfg.get("devices.asus_rt_be50.ip", "192.168.50.1"),
                username=cfg.get("devices.asus_rt_be50.username", ""),
                password=cfg.get("devices.asus_rt_be50.password", ""),
            )
        return self._asus

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(12, 12, 12, 12)

        # --- Dual WAN ---
        wan_group = QGroupBox("Dual WAN")
        wan_layout = QVBoxLayout(wan_group)

        wan_row = QHBoxLayout()
        self._wan1_label = QLabel("WAN1 (O2/Movistar HGU): —")
        self._wan2_label = QLabel("WAN2 (Vodafone CGA4233): —")
        wan_row.addWidget(self._wan1_label)
        wan_row.addWidget(self._wan2_label)
        wan_layout.addLayout(wan_row)

        btn_row = QHBoxLayout()
        btn_refresh_wan = QPushButton("Actualizar estado WAN")
        btn_refresh_wan.clicked.connect(self._refresh_wan)
        btn_row.addWidget(btn_refresh_wan)

        btn_nat = QPushButton("Subir nat-start via SSH")
        btn_nat.clicked.connect(self._upload_nat_start)
        btn_row.addWidget(btn_nat)

        btn_verify = QPushButton("Verificar configuración")
        btn_verify.clicked.connect(self._verify_config)
        btn_row.addWidget(btn_verify)
        btn_row.addStretch()
        wan_layout.addLayout(btn_row)

        layout.addWidget(wan_group)

        # --- Port Forwarding ---
        pf_group = QGroupBox("Port Forwarding")
        pf_layout = QVBoxLayout(pf_group)

        self._pf_table = QTableWidget(0, 4)
        self._pf_table.setHorizontalHeaderLabels(["Puerto ext.", "IP destino", "Puerto int.", "Protocolo"])
        self._pf_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._pf_table.setMaximumHeight(150)
        pf_layout.addWidget(self._pf_table)

        pf_btn_row = QHBoxLayout()
        btn_pf_load = QPushButton("Cargar reglas")
        btn_pf_load.clicked.connect(self._load_port_forwarding)
        pf_btn_row.addWidget(btn_pf_load)

        btn_add_443 = QPushButton("Añadir 443→8123 (HA)")
        btn_add_443.clicked.connect(lambda: self._add_pf_rule(443, "192.168.50.10", 8123))
        pf_btn_row.addWidget(btn_add_443)

        btn_add_8123 = QPushButton("Añadir 8123→8123 (HA)")
        btn_add_8123.clicked.connect(lambda: self._add_pf_rule(8123, "192.168.50.10", 8123))
        pf_btn_row.addWidget(btn_add_8123)
        pf_btn_row.addStretch()
        pf_layout.addLayout(pf_btn_row)

        layout.addWidget(pf_group)

        # --- DDNS ---
        ddns_group = QGroupBox("DDNS / DuckDNS")
        ddns_layout = QHBoxLayout(ddns_group)

        domain = cfg.get("duckdns.domain", "leonelastres.duckdns.org")
        self._ddns_label = QLabel(f"Dominio: {domain}")
        ddns_layout.addWidget(self._ddns_label)

        btn_ddns = QPushButton("Verificar que apunta a WAN1")
        btn_ddns.clicked.connect(self._verify_ddns)
        ddns_layout.addWidget(btn_ddns)
        ddns_layout.addStretch()

        layout.addWidget(ddns_group)

        # --- IP de dispositivos ---
        ip_group = QGroupBox("IPs de dispositivos")
        ip_form = QFormLayout(ip_group)

        self._ip_fields: dict[str, QLineEdit] = {}
        device_map = {
            "Asus RT-BE50":         "devices.asus_rt_be50.ip",
            "Home Assistant":       "devices.homeassistant.ip",
            "Sonoff Dongle Max":    "devices.sonoff_zigbee.ip",
            "HP Pro Mini":          "devices.hp_mini.ip",
        }
        for label, path in device_map.items():
            field = QLineEdit(cfg.get(path, ""))
            self._ip_fields[path] = field
            ip_form.addRow(label + ":", field)

        btn_save_ips = QPushButton("Guardar IPs")
        btn_save_ips.clicked.connect(self._save_ips)
        ip_form.addRow("", btn_save_ips)
        layout.addWidget(ip_group)

        layout.addStretch()

    def _refresh_wan(self) -> None:
        asus = self._get_asus()
        ok, data = asus.get_wan_ips()
        if ok:
            self._wan1_label.setText(f"WAN1 (Movistar): {data.get('wan1', '—')}")
            self._wan2_label.setText(f"WAN2 (Vodafone): {data.get('wan2', '—')}")
            self._main.log_action("Asus RT-BE50", "Consulta WAN IPs", "", str(data), "ok")
        else:
            QMessageBox.warning(self, "Error", f"No se pudo obtener IPs WAN:\n{data.get('error', data)}")

    def _upload_nat_start(self) -> None:
        if not _confirm(self, "Confirmar", "¿Subir script nat-start al router via SSH?\n\nEsto sobreescribirá el fichero actual en /jffs/scripts/nat-start."):
            return
        script = (
            "#!/bin/sh\n"
            "# nat-start — generado por Gestión Red Doméstica\n"
            "iptables -t nat -I PREROUTING -p tcp --dport 443 -j DNAT --to-destination 192.168.50.10:8123\n"
            "iptables -t nat -I PREROUTING -p tcp --dport 8123 -j DNAT --to-destination 192.168.50.10:8123\n"
        )
        asus = self._get_asus()
        ok, msg = asus.upload_nat_start(script)
        if ok:
            self._main.log_action("Asus RT-BE50", "Subir nat-start", "", script, "ok")
            QMessageBox.information(self, "Éxito", msg)
        else:
            self._main.log_action("Asus RT-BE50", "Subir nat-start", "", "", "error")
            QMessageBox.warning(self, "Error", msg)

    def _verify_config(self) -> None:
        asus = self._get_asus()
        ok, data = asus.get_dual_wan_status()
        msg = str(data) if ok else f"Error: {data}"
        QMessageBox.information(self, "Estado Dual WAN", msg)

    def _load_port_forwarding(self) -> None:
        asus = self._get_asus()
        ok, rules = asus.get_port_forwarding()
        self._pf_table.setRowCount(0)
        if not ok:
            QMessageBox.warning(self, "Error", "No se pudieron cargar las reglas de port forwarding.")
            return
        for rule in rules:
            row = self._pf_table.rowCount()
            self._pf_table.insertRow(row)
            self._pf_table.setItem(row, 0, QTableWidgetItem(str(rule.get("ext_port", ""))))
            self._pf_table.setItem(row, 1, QTableWidgetItem(str(rule.get("int_ip", ""))))
            self._pf_table.setItem(row, 2, QTableWidgetItem(str(rule.get("int_port", ""))))
            self._pf_table.setItem(row, 3, QTableWidgetItem(str(rule.get("protocol", ""))))

    def _add_pf_rule(self, ext_port: int, int_ip: str, int_port: int) -> None:
        if not _confirm(self, "Confirmar", f"¿Añadir regla de port forwarding\n{ext_port} → {int_ip}:{int_port}?"):
            return
        asus = self._get_asus()
        ok, msg = asus.add_port_forwarding(ext_port, int_ip, int_port)
        if ok:
            self._main.log_action("Asus RT-BE50", f"Port forwarding {ext_port}→{int_port}", "", f"{int_ip}:{int_port}", "ok")
            QMessageBox.information(self, "Éxito", msg)
        else:
            QMessageBox.warning(self, "Error", msg)

    def _verify_ddns(self) -> None:
        import socket as _socket
        domain = cfg.get("duckdns.domain", "leonelastres.duckdns.org")
        try:
            resolved = _socket.gethostbyname(domain)
            asus = self._get_asus()
            _, wan_data = asus.get_wan_ips()
            wan1 = wan_data.get("wan1", "")
            if wan1 and resolved == wan1:
                QMessageBox.information(self, "DDNS OK", f"{domain} → {resolved}\nCoincide con WAN1: {wan1} ✓")
            else:
                QMessageBox.warning(self, "DDNS", f"{domain} → {resolved}\nWAN1 actual: {wan1 or 'desconocida'}")
        except Exception as e:
            QMessageBox.warning(self, "Error DDNS", str(e))

    def _save_ips(self) -> None:
        if not _confirm(self, "Confirmar", "¿Guardar las IPs en config.json?"):
            return
        for path, field in self._ip_fields.items():
            cfg.set_value(path, field.text().strip())
        self._asus = None  # reset para que use las nuevas IPs
        QMessageBox.information(self, "Guardado", "IPs guardadas en config.json.")


class HomeAssistantPanel(QWidget):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self._main = main_window
        self._ha: HomeAssistantAPI | None = None
        self._build_ui()

    def _get_ha(self) -> HomeAssistantAPI:
        if self._ha is None:
            self._ha = HomeAssistantAPI(
                ip=cfg.get("devices.homeassistant.ip", "192.168.50.10"),
                port=cfg.get("devices.homeassistant.port", 8123),
                token=cfg.get("devices.homeassistant.token", ""),
            )
        return self._ha

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(12, 12, 12, 12)

        # --- Estado conexión ---
        conn_group = QGroupBox("Conexión a Home Assistant")
        conn_layout = QHBoxLayout(conn_group)
        self._conn_label = QLabel("Estado: desconocido")
        conn_layout.addWidget(self._conn_label)
        btn_check = QPushButton("Comprobar conexión")
        btn_check.clicked.connect(self._check_connection)
        conn_layout.addWidget(btn_check)

        btn_open = QPushButton("Abrir en navegador")
        btn_open.clicked.connect(lambda: self._get_ha().open_browser())
        conn_layout.addWidget(btn_open)
        conn_layout.addStretch()
        layout.addWidget(conn_group)

        # --- Token ---
        token_group = QGroupBox("Token de larga duración")
        token_form = QFormLayout(token_group)
        self._token_field = QLineEdit(cfg.get("devices.homeassistant.token", ""))
        self._token_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._token_field.setPlaceholderText("Pega aquí tu token de HA")
        token_form.addRow("Token:", self._token_field)
        btn_save_token = QPushButton("Guardar token")
        btn_save_token.clicked.connect(self._save_token)
        token_form.addRow("", btn_save_token)
        layout.addWidget(token_group)

        # --- ZHA ---
        zha_group = QGroupBox("Configuración ZHA / Zigbee")
        zha_layout = QVBoxLayout(zha_group)
        self._zha_label = QLabel("Ruta serial ZHA: —")
        zha_layout.addWidget(self._zha_label)

        zha_btn_row = QHBoxLayout()
        btn_get_zha = QPushButton("Obtener config ZHA")
        btn_get_zha.clicked.connect(self._get_zha)
        zha_btn_row.addWidget(btn_get_zha)

        btn_set_socket = QPushButton("Cambiar a socket://192.168.50.5:6638")
        btn_set_socket.clicked.connect(self._set_zha_socket)
        zha_btn_row.addWidget(btn_set_socket)
        zha_btn_row.addStretch()
        zha_layout.addLayout(zha_btn_row)
        layout.addWidget(zha_group)

        # --- URL externa ---
        url_group = QGroupBox("URL Externa")
        url_layout = QVBoxLayout(url_group)
        self._ext_url_label = QLabel("URL externa: —")
        url_layout.addWidget(self._ext_url_label)

        url_btn_row = QHBoxLayout()
        btn_get_url = QPushButton("Obtener URL actual")
        btn_get_url.clicked.connect(self._get_ext_url)
        url_btn_row.addWidget(btn_get_url)

        target_domain = cfg.get("duckdns.domain", "leonelastres.duckdns.org")
        btn_set_url = QPushButton(f"Actualizar a https://{target_domain}")
        btn_set_url.clicked.connect(lambda: self._set_ext_url(f"https://{target_domain}"))
        url_btn_row.addWidget(btn_set_url)
        url_btn_row.addStretch()
        url_layout.addLayout(url_btn_row)

        self._instructions_box = QTextEdit()
        self._instructions_box.setReadOnly(True)
        self._instructions_box.setMaximumHeight(120)
        self._instructions_box.setVisible(False)
        url_layout.addWidget(self._instructions_box)

        layout.addWidget(url_group)
        layout.addStretch()

    def _check_connection(self) -> None:
        ok = self._get_ha().check_connection()
        if ok:
            self._conn_label.setText("Estado: conectado ✓")
            self._conn_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self._main.log_action("Home Assistant", "Comprobar conexión", "", "ok", "ok")
        else:
            self._conn_label.setText("Estado: sin conexión ✗")
            self._conn_label.setStyleSheet("color: #f38ba8; font-weight: bold;")
            self._main.log_action("Home Assistant", "Comprobar conexión", "", "error", "error")

    def _save_token(self) -> None:
        if not _confirm(self, "Confirmar", "¿Guardar el token en config.json?"):
            return
        token = self._token_field.text().strip()
        cfg.set_value("devices.homeassistant.token", token)
        self._ha = None
        QMessageBox.information(self, "Guardado", "Token guardado. Se usará en la próxima conexión.")

    def _get_zha(self) -> None:
        ok, data = self._get_ha().get_zha_config()
        if ok:
            serial = data.get("data", {}).get("device", data.get("options", {}).get("device_path", "—"))
            self._zha_label.setText(f"Ruta serial ZHA: {serial}")
        else:
            err = data.get("error", str(data)) if isinstance(data, dict) else str(data)
            self._zha_label.setText(f"ZHA: {err}")

    def _set_zha_socket(self) -> None:
        if not _confirm(self, "Confirmar",
                        "¿Cambiar la ruta del coordinador ZHA a:\nsocket://192.168.50.5:6638?\n\n"
                        "Esto requiere reiniciar la integración ZHA en Home Assistant."):
            return
        old = self._zha_label.text()
        # La API de HA no permite cambiar el device path directamente vía REST
        # Se muestra instrucción al usuario
        instrucciones = (
            "Para cambiar el coordinador ZHA:\n"
            "1. Abre Home Assistant → Ajustes → Dispositivos e integraciones\n"
            "2. Busca la integración ZHA y pulsa 'Configurar'\n"
            "3. En 'Serial device path' escribe:\n"
            "   socket://192.168.50.5:6638\n"
            "4. Guarda y reinicia la integración."
        )
        QMessageBox.information(self, "Instrucciones ZHA", instrucciones)
        self._main.log_action("Home Assistant", "Cambiar ZHA a socket", old, "socket://192.168.50.5:6638", "info")

    def _get_ext_url(self) -> None:
        ok, url = self._get_ha().get_external_url()
        if ok:
            self._ext_url_label.setText(f"URL externa: {url or '(no configurada)'}")
        else:
            self._ext_url_label.setText(f"URL externa: {url}")

    def _set_ext_url(self, url: str) -> None:
        if not _confirm(self, "Confirmar", f"¿Establecer la URL externa a:\n{url}?"):
            return
        _, instrucciones = self._get_ha().set_external_url(url)
        self._instructions_box.setText(instrucciones)
        self._instructions_box.setVisible(True)
        self._main.log_action("Home Assistant", "Establecer URL externa", "", url, "info")


class SonoffPanel(QWidget):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self._main = main_window
        self._sonoff: SonoffZigbee | None = None
        self._build_ui()

    def _get_sonoff(self) -> SonoffZigbee:
        if self._sonoff is None:
            self._sonoff = SonoffZigbee(
                ip=cfg.get("devices.sonoff_zigbee.ip", "192.168.50.5"),
                zha_port=cfg.get("devices.sonoff_zigbee.zha_port", 6638),
            )
        return self._sonoff

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(12, 12, 12, 12)

        status_group = QGroupBox("Estado del Dongle")
        status_layout = QVBoxLayout(status_group)

        info_row = QHBoxLayout()
        ip_label = QLabel(f"IP: {cfg.get('devices.sonoff_zigbee.ip', '192.168.50.5')}")
        info_row.addWidget(ip_label)
        port_label = QLabel(f"Puerto ZHA: {cfg.get('devices.sonoff_zigbee.zha_port', 6638)}")
        info_row.addWidget(port_label)
        info_row.addStretch()
        status_layout.addLayout(info_row)

        self._tcp_label = QLabel("TCP puerto 6638: —")
        self._http_label = QLabel("Interfaz web (HTTP): —")
        self._coordinator_label = QLabel("Coordinador Zigbee: —")
        status_layout.addWidget(self._tcp_label)
        status_layout.addWidget(self._http_label)
        status_layout.addWidget(self._coordinator_label)

        btn_row = QHBoxLayout()
        btn_check = QPushButton("Comprobar estado")
        btn_check.clicked.connect(self._check_status)
        btn_row.addWidget(btn_check)

        btn_web = QPushButton("Abrir interfaz web")
        btn_web.clicked.connect(lambda: self._get_sonoff().open_browser())
        btn_row.addWidget(btn_web)
        btn_row.addStretch()
        status_layout.addLayout(btn_row)

        layout.addWidget(status_group)
        layout.addStretch()

    def _check_status(self) -> None:
        status = self._get_sonoff().get_status()
        tcp = status["tcp"]
        http = status["http"]

        color_ok = "color: #a6e3a1;"
        color_err = "color: #f38ba8;"

        self._tcp_label.setText(f"TCP puerto 6638: {tcp['message']}")
        self._tcp_label.setStyleSheet(color_ok if tcp["ok"] else color_err)

        self._http_label.setText(f"Interfaz web (HTTP): {http['message']}")
        self._http_label.setStyleSheet(color_ok if http["ok"] else color_err)

        self._coordinator_label.setText(f"Coordinador Zigbee: {status['coordinator']}")
        self._coordinator_label.setStyleSheet(color_ok if tcp["ok"] else color_err)

        self._main.log_action("Sonoff Dongle Max", "Comprobar estado", "", str(status), "ok")


class HPMiniPanel(QWidget):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self._main = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(12, 12, 12, 12)

        status_group = QGroupBox("Estado HP Pro Mini 400 G9")
        status_layout = QVBoxLayout(status_group)

        ip = cfg.get("devices.hp_mini.ip", "192.168.50.20")
        status_layout.addWidget(QLabel(f"IP: {ip}"))

        self._status_label = QLabel("Estado: —")
        status_layout.addWidget(self._status_label)

        btn_row = QHBoxLayout()
        btn_ping = QPushButton("Comprobar (ping)")
        btn_ping.clicked.connect(self._check_ping)
        btn_row.addWidget(btn_ping)

        btn_smb = QPushButton("Abrir Explorador de archivos compartidos")
        btn_smb.clicked.connect(self._open_smb)
        btn_row.addWidget(btn_smb)
        btn_row.addStretch()
        status_layout.addLayout(btn_row)

        layout.addWidget(status_group)
        layout.addStretch()

    def _check_ping(self) -> None:
        import subprocess, platform
        ip = cfg.get("devices.hp_mini.ip", "192.168.50.20")
        system = platform.system().lower()
        cmd = ["ping", "-n", "1", "-w", "1000", ip] if system == "windows" else ["ping", "-c", "1", "-W", "2", ip]
        try:
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            if result.returncode == 0:
                self._status_label.setText("Estado: en línea ✓")
                self._status_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            else:
                self._status_label.setText("Estado: fuera de línea ✗")
                self._status_label.setStyleSheet("color: #f38ba8; font-weight: bold;")
        except Exception as e:
            self._status_label.setText(f"Error: {e}")

    def _open_smb(self) -> None:
        import subprocess, platform, webbrowser
        ip = cfg.get("devices.hp_mini.ip", "192.168.50.20")
        system = platform.system().lower()
        smb_url = f"smb://{ip}"
        if system == "windows":
            subprocess.Popen(["explorer", f"\\\\{ip}"])
        elif system == "darwin":
            subprocess.Popen(["open", smb_url])
        else:
            # Linux: intentar con el gestor de ficheros
            try:
                subprocess.Popen(["xdg-open", smb_url])
            except Exception:
                webbrowser.open(smb_url)


class ConfigTab(QWidget):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self._main = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Dispositivo:"))

        self._device_combo = QComboBox()
        self._device_combo.addItems([
            "Asus RT-BE50",
            "Home Assistant (HAOS)",
            "Sonoff Dongle Max",
            "HP Pro Mini 400 G9",
        ])
        self._device_combo.currentIndexChanged.connect(self._switch_panel)
        selector_row.addWidget(self._device_combo)
        selector_row.addStretch()
        layout.addLayout(selector_row)

        self._stack = QStackedWidget()
        self._stack.addWidget(AsusPanel(self._main))
        self._stack.addWidget(HomeAssistantPanel(self._main))
        self._stack.addWidget(SonoffPanel(self._main))
        self._stack.addWidget(HPMiniPanel(self._main))
        layout.addWidget(self._stack)

    def _switch_panel(self, index: int) -> None:
        self._stack.setCurrentIndex(index)

    def show_device(self, index: int) -> None:
        self._device_combo.setCurrentIndex(index)
        self._stack.setCurrentIndex(index)
