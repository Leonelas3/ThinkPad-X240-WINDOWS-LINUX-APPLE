import socket
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


KNOWN_DEVICES: dict[str, dict] = {
    "192.168.50.1":  {"name": "Asus RT-BE50",          "type": "router"},
    "192.168.50.10": {"name": "ThinkPad X250 (HAOS)",  "type": "homeassistant"},
    "192.168.50.20": {"name": "HP Pro Mini 400 G9",     "type": "pc"},
    "192.168.50.5":  {"name": "Sonoff Dongle Max",      "type": "zigbee"},
}

KNOWN_PORTS = [22, 80, 443, 8123, 6638]


@dataclass
class DeviceInfo:
    ip: str
    hostname: str = ""
    open_ports: list[int] = field(default_factory=list)
    is_known: bool = False
    device_type: str = "unknown"
    device_name: str = ""


class NetworkScanner(QObject):
    device_found = pyqtSignal(object)
    scan_finished = pyqtSignal(list)
    scan_progress = pyqtSignal(int, int)

    def __init__(self, subnet_base: str = "192.168.50", parent=None):
        super().__init__(parent)
        self._subnet_base = subnet_base
        self._running = False

    def stop(self) -> None:
        self._running = False

    def scan(self) -> list[DeviceInfo]:
        self._running = True
        ips = [f"{self._subnet_base}.{i}" for i in range(1, 255)]
        results: list[DeviceInfo] = []
        total = len(ips)
        done = 0

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(self._probe_ip, ip): ip for ip in ips}
            for future in as_completed(futures):
                if not self._running:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                done += 1
                self.scan_progress.emit(done, total)
                result = future.result()
                if result is not None:
                    results.append(result)
                    self.device_found.emit(result)

        self._running = False
        self.scan_finished.emit(results)
        return results

    def _probe_ip(self, ip: str) -> Optional[DeviceInfo]:
        if not self._ping(ip):
            return None

        hostname = self._resolve_hostname(ip)
        open_ports = self._check_ports(ip)
        known = KNOWN_DEVICES.get(ip)

        return DeviceInfo(
            ip=ip,
            hostname=hostname,
            open_ports=open_ports,
            is_known=known is not None,
            device_type=known["type"] if known else "unknown",
            device_name=known["name"] if known else "",
        )

    @staticmethod
    def _ping(ip: str) -> bool:
        system = platform.system().lower()
        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", "500", ip]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", ip]
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def _check_ports(ip: str) -> list[int]:
        open_ports = []
        for port in KNOWN_PORTS:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex((ip, port)) == 0:
                        open_ports.append(port)
            except Exception:
                pass
        return open_ports

    @staticmethod
    def _resolve_hostname(ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ""
