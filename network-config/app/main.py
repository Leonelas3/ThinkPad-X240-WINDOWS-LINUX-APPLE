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
_ensure_package("PyQt6-WebEngine", "PyQt6.QtWebEngineWidgets")
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

    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    if first_run:
        from gui.setup_wizard import SetupWizard
        wizard = SetupWizard(window)
        wizard.exec()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
