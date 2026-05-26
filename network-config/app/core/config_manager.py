import json
import shutil
from pathlib import Path
from typing import Any


_APP_DIR = Path(__file__).parent.parent
_CONFIG_PATH = _APP_DIR / "config.json"
_EXAMPLE_PATH = _APP_DIR / "config.example.json"

_config: dict = {}
_first_run = False


def load() -> bool:
    global _config, _first_run
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _config = json.load(f)
        return True

    # config.json no existe: copiamos el ejemplo y avisamos
    shutil.copy(_EXAMPLE_PATH, _CONFIG_PATH)
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        _config = json.load(f)
    _first_run = True
    return False


def is_first_run() -> bool:
    return _first_run


def get(path: str, default: Any = None) -> Any:
    keys = path.split(".")
    node = _config
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            return default
        node = node[k]
    return node


def set_value(path: str, value: Any) -> None:
    keys = path.split(".")
    node = _config
    for k in keys[:-1]:
        node = node.setdefault(k, {})
    node[keys[-1]] = value
    _save()


def _save() -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(_config, f, indent=2, ensure_ascii=False)


def get_all() -> dict:
    return _config
