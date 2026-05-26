import base64
import socket
from typing import Optional

try:
    import requests
    import paramiko
except ImportError:
    requests = None
    paramiko = None


class AsusRT_BE50:
    def __init__(self, ip: str, username: str, password: str):
        self._ip = ip
        self._username = username
        self._password = password
        self._session: Optional[object] = None
        self._base_url = f"http://{ip}"

    def _ensure_requests(self) -> tuple[bool, str]:
        if requests is None:
            return False, "Módulo 'requests' no disponible"
        return True, ""

    def login(self) -> tuple[bool, str]:
        ok, msg = self._ensure_requests()
        if not ok:
            return False, msg
        try:
            token = base64.b64encode(
                f"{self._username}:{self._password}".encode()
            ).decode()
            session = requests.Session()
            resp = session.post(
                f"{self._base_url}/login.cgi",
                data={"login_authorization": token},
                timeout=10,
                verify=False,
            )
            if resp.status_code == 200 and "asus_token" in session.cookies:
                self._session = session
                return True, "Sesión iniciada correctamente"
            return False, f"Login fallido (HTTP {resp.status_code})"
        except requests.exceptions.ConnectionError:
            return False, f"No se puede conectar a {self._base_url}"
        except Exception as e:
            return False, str(e)

    def get_dual_wan_status(self) -> tuple[bool, dict]:
        if self._session is None:
            ok, msg = self.login()
            if not ok:
                return False, {"error": msg}
        try:
            resp = self._session.get(
                f"{self._base_url}/appGet.cgi",
                params={"hook": "get_dualwan_info()"},
                timeout=10,
                verify=False,
            )
            if resp.status_code != 200:
                return False, {"error": f"HTTP {resp.status_code}"}

            data = resp.text
            result = {"raw": data, "wan1": "desconocido", "wan2": "desconocido"}

            # La respuesta de AsusWRT viene en formato propio; intentamos parsear
            for line in data.splitlines():
                if "wan1" in line.lower() or "primary" in line.lower():
                    result["wan1"] = line.strip()
                if "wan2" in line.lower() or "secondary" in line.lower():
                    result["wan2"] = line.strip()

            return True, result
        except Exception as e:
            return False, {"error": str(e)}

    def get_wan_ips(self) -> tuple[bool, dict]:
        if self._session is None:
            ok, msg = self.login()
            if not ok:
                return False, {"error": msg}
        try:
            resp = self._session.get(
                f"{self._base_url}/appGet.cgi",
                params={"hook": "nvram_get(wan0_ipaddr);nvram_get(wan1_ipaddr)"},
                timeout=10,
                verify=False,
            )
            if resp.status_code != 200:
                return False, {"error": f"HTTP {resp.status_code}"}

            result = {"wan1": "", "wan2": "", "raw": resp.text}
            for line in resp.text.splitlines():
                if "wan0_ipaddr" in line:
                    result["wan1"] = line.split("=")[-1].strip().strip('"')
                if "wan1_ipaddr" in line:
                    result["wan2"] = line.split("=")[-1].strip().strip('"')
            return True, result
        except Exception as e:
            return False, {"error": str(e)}

    def upload_nat_start(self, script_content: str) -> tuple[bool, str]:
        if paramiko is None:
            return False, "Módulo 'paramiko' no disponible"
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                self._ip,
                username=self._username,
                password=self._password,
                timeout=15,
                look_for_keys=False,
                allow_agent=False,
            )
            sftp = client.open_sftp()
            with sftp.open("/jffs/scripts/nat-start", "w") as f:
                f.write(script_content)
            sftp.close()
            _, stdout, stderr = client.exec_command("chmod +x /jffs/scripts/nat-start")
            stdout.channel.recv_exit_status()
            client.close()
            return True, "Script nat-start subido y marcado como ejecutable"
        except paramiko.AuthenticationException:
            return False, "Credenciales SSH incorrectas"
        except paramiko.SSHException as e:
            return False, f"Error SSH: {e}"
        except socket.timeout:
            return False, f"Timeout al conectar por SSH a {self._ip}"
        except Exception as e:
            return False, str(e)

    def get_port_forwarding(self) -> tuple[bool, list[dict]]:
        if self._session is None:
            ok, msg = self.login()
            if not ok:
                return False, []
        try:
            resp = self._session.get(
                f"{self._base_url}/appGet.cgi",
                params={"hook": "nvram_get(vts_rulelist)"},
                timeout=10,
                verify=False,
            )
            if resp.status_code != 200:
                return False, []

            rules = []
            raw = resp.text
            # Formato típico: <ext_port>><int_ip>><int_port>><proto>><desc>
            for entry in raw.split("<"):
                parts = entry.strip(">").split(">")
                if len(parts) >= 4:
                    rules.append({
                        "ext_port": parts[0],
                        "int_ip":   parts[1],
                        "int_port": parts[2],
                        "protocol": parts[3],
                    })
            return True, rules
        except Exception as e:
            return False, []

    def add_port_forwarding(
        self, ext_port: int, int_ip: str, int_port: int, protocol: str = "TCP"
    ) -> tuple[bool, str]:
        if self._session is None:
            ok, msg = self.login()
            if not ok:
                return False, msg
        try:
            resp = self._session.post(
                f"{self._base_url}/applyapp.cgi",
                data={
                    "action_mode": "apply",
                    "action_script": "restart_firewall",
                    "action_wait": "5",
                    "vts_enable_x": "1",
                    "vts_rulelist": f"<{ext_port}>{int_ip}>{int_port}>{protocol}>Regla_app",
                },
                timeout=15,
                verify=False,
            )
            if resp.status_code == 200:
                return True, f"Regla {ext_port}→{int_ip}:{int_port} añadida"
            return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, str(e)
