from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable


class Level(Enum):
    INFO    = "info"
    WARNING = "warning"
    ERROR   = "error"


@dataclass
class Notification:
    level:        Level
    title:        str
    message:      str
    timestamp:    str          = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    action_label: str | None   = None
    action:       Callable | None = None
    read:         bool         = False


_store:     list[Notification] = []
_listeners: list[Callable]     = []


def add(
    level:        Level,
    title:        str,
    message:      str,
    action_label: str | None    = None,
    action:       Callable | None = None,
) -> None:
    n = Notification(level, title, message, action_label=action_label, action=action)
    _store.append(n)
    for cb in _listeners:
        try:
            cb(n)
        except Exception:
            pass


def get_all() -> list[Notification]:
    return list(_store)


def unread_count() -> int:
    return sum(1 for n in _store if not n.read)


def mark_all_read() -> None:
    for n in _store:
        n.read = True


def subscribe(callback: Callable) -> None:
    _listeners.append(callback)
