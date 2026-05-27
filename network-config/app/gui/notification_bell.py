from __future__ import annotations
import subprocess, sys

from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QToolButton, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QScrollArea, QApplication, QSizePolicy,
)

import core.notifications as notif
from core.notifications import Level


_LEVEL_ICON  = {Level.INFO: "ℹ️", Level.WARNING: "⚠️", Level.ERROR: "❌"}
_LEVEL_COLOR = {Level.INFO: "#4a9eff", Level.WARNING: "#f9e2af", Level.ERROR: "#f38ba8"}


class _Item(QFrame):
    def __init__(self, n: notif.Notification):
        super().__init__()
        self.setObjectName("notif_item")
        self.setStyleSheet(
            "#notif_item { background: #2a2a3e; border-radius: 6px; margin: 2px 4px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        top = QHBoxLayout()
        icon = QLabel(_LEVEL_ICON[n.level])
        icon.setFixedWidth(18)
        title = QLabel(f"<b>{n.title}</b>")
        title.setStyleSheet(f"color: {_LEVEL_COLOR[n.level]};")
        ts = QLabel(n.timestamp)
        ts.setStyleSheet("color: #6c7086; font-size: 10px;")
        ts.setAlignment(Qt.AlignmentFlag.AlignRight)
        top.addWidget(icon)
        top.addWidget(title, stretch=1)
        top.addWidget(ts)
        layout.addLayout(top)

        msg = QLabel(n.message)
        msg.setStyleSheet("color: #cdd6f4; font-size: 11px;")
        msg.setWordWrap(True)
        layout.addWidget(msg)

        if n.action_label and n.action:
            btn = QPushButton(n.action_label)
            btn.setFixedHeight(24)
            btn.setStyleSheet(
                "QPushButton { background:#3a3a5e; color:#4a9eff; border:none; "
                "border-radius:4px; padding:0 8px; font-size:11px; } "
                "QPushButton:hover { background:#4a4a6e; }"
            )
            btn.clicked.connect(n.action)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignLeft)


class _Popup(QFrame):
    def __init__(self, parent: QWidget):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFixedWidth(340)
        self.setMaximumHeight(480)
        self.setStyleSheet(
            "QFrame { background: #1e1e2e; border: 1px solid #3a3a5e; border-radius: 8px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        lbl = QLabel("  Notificaciones")
        lbl.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 13px;")
        btn_clear = QPushButton("Marcar leídas")
        btn_clear.setFixedHeight(22)
        btn_clear.setStyleSheet(
            "QPushButton { background: transparent; color: #6c7086; border: none; "
            "font-size: 11px; } QPushButton:hover { color: #4a9eff; }"
        )
        btn_clear.clicked.connect(self._mark_read)
        header.addWidget(lbl, stretch=1)
        header.addWidget(btn_clear)
        layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #3a3a5e;")
        layout.addWidget(sep)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(self._scroll)

        self._rebuild()

    def _rebuild(self) -> None:
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        items = notif.get_all()
        if not items:
            empty = QLabel("Sin notificaciones")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #6c7086; padding: 20px;")
            vbox.addWidget(empty)
        else:
            for n in reversed(items):
                vbox.addWidget(_Item(n))

        vbox.addStretch()
        self._scroll.setWidget(container)

    def _mark_read(self) -> None:
        notif.mark_all_read()
        self._rebuild()

    def showEvent(self, event) -> None:
        self._rebuild()
        super().showEvent(event)


class NotificationBell(QWidget):
    """Campanita en la toolbar con badge de no leídos y popup desplegable."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(36, 36)

        self._btn = QToolButton(self)
        self._btn.setText("🔔")
        self._btn.setFixedSize(36, 36)
        self._btn.setStyleSheet(
            "QToolButton { background: transparent; border: none; font-size: 16px; } "
            "QToolButton:hover { background: #2a2a3e; border-radius: 6px; }"
        )
        self._btn.clicked.connect(self._toggle_popup)

        self._badge = QLabel(self)
        self._badge.setFixedSize(16, 16)
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setStyleSheet(
            "background: #f38ba8; color: #1e1e2e; border-radius: 8px; "
            "font-size: 9px; font-weight: bold;"
        )
        self._badge.move(20, 2)
        self._badge.hide()

        self._popup: _Popup | None = None

        notif.subscribe(self._on_new_notification)
        self._refresh_badge()

    def _on_new_notification(self, _: notif.Notification) -> None:
        self._refresh_badge()
        # Animación rápida: parpadeo del badge
        QTimer.singleShot(0,   lambda: self._badge.setStyleSheet(
            "background:#f38ba8;color:#1e1e2e;border-radius:8px;font-size:9px;font-weight:bold;"))
        QTimer.singleShot(200, lambda: self._badge.setStyleSheet(
            "background:#fab387;color:#1e1e2e;border-radius:8px;font-size:9px;font-weight:bold;"))
        QTimer.singleShot(400, lambda: self._badge.setStyleSheet(
            "background:#f38ba8;color:#1e1e2e;border-radius:8px;font-size:9px;font-weight:bold;"))

    def _refresh_badge(self) -> None:
        count = notif.unread_count()
        if count > 0:
            self._badge.setText(str(min(count, 99)))
            self._badge.show()
        else:
            self._badge.hide()

    def _toggle_popup(self) -> None:
        if self._popup and self._popup.isVisible():
            self._popup.hide()
            return

        notif.mark_all_read()
        self._refresh_badge()

        if self._popup is None:
            # El popup es hijo de la ventana principal para posicionarlo bien
            top = self.window()
            self._popup = _Popup(top)

        btn_global = self._btn.mapToGlobal(QPoint(0, self._btn.height() + 2))
        # Ajustar si se sale de la pantalla
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            x = min(btn_global.x(), sg.right() - self._popup.width() - 8)
            btn_global = QPoint(x, btn_global.y())

        self._popup.move(btn_global)
        self._popup.show()
        self._popup.raise_()
