from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QComboBox, QFileDialog,
    QMessageBox, QAbstractItemView,
)

import core.db as db

if TYPE_CHECKING:
    from gui.main_window import MainWindow


class LogTab(QWidget):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self._main = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()

        toolbar.addWidget(QLabel("Filtrar por dispositivo:"))
        self._filter_combo = QComboBox()
        self._filter_combo.addItem("Todos")
        self._filter_combo.currentTextChanged.connect(self._apply_filter)
        toolbar.addWidget(self._filter_combo)

        toolbar.addStretch()

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(btn_refresh)

        btn_export = QPushButton("📄 Exportar CSV")
        btn_export.clicked.connect(self._export_csv)
        toolbar.addWidget(btn_export)

        btn_cleanup = QPushButton("🗑 Limpiar >30 días")
        btn_cleanup.clicked.connect(self._cleanup_old)
        toolbar.addWidget(btn_cleanup)

        layout.addLayout(toolbar)

        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels([
            "ID", "Fecha/Hora", "Dispositivo", "Acción", "Valor anterior", "Valor nuevo", "Estado"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        self.load_data()

    def load_data(self, device_filter: str | None = None) -> None:
        if device_filter == "Todos":
            device_filter = None

        rows = db.get_all(device_filter)
        self._table.setRowCount(0)

        devices_seen: set[str] = set()
        for row_data in rows:
            devices_seen.add(row_data["device"])
            row = self._table.rowCount()
            self._table.insertRow(row)

            self._table.setItem(row, 0, QTableWidgetItem(str(row_data["id"])))
            self._table.setItem(row, 1, QTableWidgetItem(row_data["timestamp"]))
            self._table.setItem(row, 2, QTableWidgetItem(row_data["device"]))
            self._table.setItem(row, 3, QTableWidgetItem(row_data["action"]))
            self._table.setItem(row, 4, QTableWidgetItem(row_data["old_value"] or ""))
            self._table.setItem(row, 5, QTableWidgetItem(row_data["new_value"] or ""))

            status = row_data["status"] or "ok"
            status_item = QTableWidgetItem(status)
            if status == "ok":
                status_item.setForeground(
                    __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor("#a6e3a1")
                )
            elif status == "error":
                status_item.setForeground(
                    __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor("#f38ba8")
                )
            elif status in ("info", "revertido"):
                status_item.setForeground(
                    __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor("#f9e2af")
                )
            self._table.setItem(row, 6, status_item)

        # Actualizar filtro de dispositivos
        current_filter = self._filter_combo.currentText()
        self._filter_combo.blockSignals(True)
        self._filter_combo.clear()
        self._filter_combo.addItem("Todos")
        for dev in sorted(devices_seen):
            self._filter_combo.addItem(dev)
        idx = self._filter_combo.findText(current_filter)
        self._filter_combo.setCurrentIndex(max(0, idx))
        self._filter_combo.blockSignals(False)

    def _apply_filter(self, text: str) -> None:
        self.load_data(None if text == "Todos" else text)

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar historial", "historial_red.csv", "CSV (*.csv)"
        )
        if not path:
            return
        ok, result = db.export_csv(path)
        if ok:
            QMessageBox.information(self, "Exportado", f"Historial exportado a:\n{result}")
        else:
            QMessageBox.warning(self, "Error", f"No se pudo exportar:\n{result}")

    def _cleanup_old(self) -> None:
        reply = QMessageBox.question(
            self,
            "Limpiar historial",
            "¿Eliminar todas las entradas de hace más de 30 días?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        deleted = db.cleanup_old(30)
        self.load_data()
        QMessageBox.information(self, "Limpieza completa", f"Se eliminaron {deleted} entradas antiguas.")
