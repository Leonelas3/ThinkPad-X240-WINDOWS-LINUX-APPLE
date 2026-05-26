import sys
import subprocess


def _ensure_package(package: str, import_name: str | None = None) -> None:
    mod = import_name or package
    try:
        __import__(mod)
    except ImportError:
        print(f"[setup] Instalando {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


_ensure_package("PyQt6")
_ensure_package("requests")
_ensure_package("paramiko")

import core.db as db
import core.config_manager as cfg

from PyQt6.QtWidgets import QApplication, QMessageBox


def main() -> None:
    db.init_db()
    first_run = not cfg.load()

    app = QApplication(sys.argv)
    app.setApplicationName("Gestión Red Doméstica")
    app.setOrganizationName("LeoNelastres")

    if first_run:
        QMessageBox.information(
            None,
            "Primera ejecución",
            "No se encontró config.json.\n\n"
            "Se ha creado una copia desde config.example.json.\n"
            "Por favor, edita config.json y rellena tus credenciales antes de usar las funciones que requieren autenticación.",
        )

    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
