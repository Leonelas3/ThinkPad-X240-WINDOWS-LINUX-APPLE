import socket
import webbrowser

try:
    import requests
except ImportError:
    requests = None


class SonoffZigbee:
    def __init__(self, ip: str, zha_port: int = 6638):
        self._ip = ip
        self._port = zha_port

    def check_tcp_port(self) -> tuple[bool, str]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex((self._ip, self._port))
                if result == 0:
                    return True, f"Puerto {self._port} accesible"
                return False, f"Puerto {self._port} cerrado (código {result})"
        except socket.timeout:
            return False, f"Timeout conectando a {self._ip}:{self._port}"
        except Exception as e:
            return False, str(e)

    def check_http(self) -> tuple[bool, str]:
        if requests is None:
            return False, "Módulo 'requests' no disponible"
        try:
            resp = requests.get(f"http://{self._ip}/", timeout=5)
            if resp.status_code < 400:
                return True, f"Interfaz web accesible (HTTP {resp.status_code})"
            return False, f"HTTP {resp.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "No responde en el puerto 80"
        except requests.exceptions.Timeout:
            return False, "Timeout en interfaz web"
        except Exception as e:
            return False, str(e)

    def get_status(self) -> dict:
        tcp_ok, tcp_msg = self.check_tcp_port()
        http_ok, http_msg = self.check_http()
        return {
            "online": tcp_ok or http_ok,
            "tcp": {"ok": tcp_ok, "message": tcp_msg},
            "http": {"ok": http_ok, "message": http_msg},
            "coordinator": "activo" if tcp_ok else "no accesible",
        }

    def open_browser(self) -> None:
        webbrowser.open(f"http://{self._ip}")
