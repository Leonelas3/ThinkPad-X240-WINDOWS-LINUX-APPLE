import webbrowser

try:
    import requests
except ImportError:
    requests = None


class HomeAssistantAPI:
    def __init__(self, ip: str, port: int, token: str):
        self._base = f"http://{ip}:{port}"
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, timeout: int = 10):
        if requests is None:
            raise RuntimeError("Módulo 'requests' no disponible")
        return requests.get(f"{self._base}{path}", headers=self._headers, timeout=timeout)

    def check_connection(self) -> bool:
        try:
            resp = self._get("/api/")
            return resp.status_code == 200
        except Exception:
            return False

    def get_zha_config(self) -> tuple[bool, dict]:
        try:
            resp = self._get("/api/config/config_entries/entry")
            if resp.status_code != 200:
                return False, {}
            entries = resp.json()
            for entry in entries:
                if entry.get("domain") == "zha":
                    return True, entry
            return False, {"error": "Integración ZHA no encontrada"}
        except Exception as e:
            return False, {"error": str(e)}

    def get_external_url(self) -> tuple[bool, str]:
        try:
            resp = self._get("/api/config")
            if resp.status_code != 200:
                return False, ""
            data = resp.json()
            url = data.get("external_url") or data.get("external_url_preference", "")
            return True, url
        except Exception as e:
            return False, str(e)

    def set_external_url(self, url: str) -> tuple[bool, str]:
        # En HAOS no hay API directa para cambiar external_url;
        # hay que editar configuration.yaml o usar la UI de HA.
        instrucciones = (
            f"Para establecer la URL externa a '{url}' en Home Assistant OS:\n\n"
            "1. Abre Home Assistant → Ajustes → Sistema → Red\n"
            "2. En 'URL externa' escribe: " + url + "\n"
            "3. Guarda los cambios.\n\n"
            "Alternativamente, edita configuration.yaml y añade:\n"
            "homeassistant:\n"
            f"  external_url: \"{url}\""
        )
        return False, instrucciones

    def get_config_entries(self) -> tuple[bool, list]:
        try:
            resp = self._get("/api/config/config_entries/entry")
            if resp.status_code == 200:
                return True, resp.json()
            return False, []
        except Exception as e:
            return False, []

    def open_browser(self) -> None:
        webbrowser.open(self._base)
