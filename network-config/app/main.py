import sys
import subprocess

# Packages that failed to auto-install — posted as notifications after GUI loads
_failed_installs: list[tuple[str, str]] = []  # (package, import_name)


def _ensure_package(package: str, import_name: str | None = None) -> None:
    mod = import_name or package
    try:
        __import__(mod)
        return
    except ImportError:
        pass

    print(f"[setup] Instalando {package}...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            timeout=120,
        )
        __import__(mod)
        print(f"[setup] {package} instalado correctamente.")
    except Exception as exc:
        print(f"[setup] No se pudo instalar {package}: {exc}")
        _failed_installs.append((package, mod))


_ensure_package("PyQt6")
_ensure_package("PyQt6-WebEngine", "PyQt6.QtWebEngineWidgets")
_ensure_package("requests")
_ensure_package("paramiko")

import core.db as db
import core.config_manager as cfg

from PyQt6.QtWidgets import QApplication


def _post_pending_notifications() -> None:
    """Convert any install failures into notification-center entries."""
    if not _failed_installs:
        return

    import core.notifications as notif
    from core.notifications import Level

    for package, mod in _failed_installs:
        def _make_retry(pkg: str, imp: str):
            def _retry():
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "--quiet", pkg],
                        timeout=120,
                    )
                    notif.add(
                        Level.INFO,
                        f"{pkg} instalado",
                        f"Paquete instalado correctamente. Reinicia la aplicación para activarlo.",
                    )
                except Exception as exc:
                    notif.add(
                        Level.ERROR,
                        f"Fallo al instalar {pkg}",
                        f"Ejecuta manualmente: pip install {pkg}\nError: {exc}",
                    )
            return _retry

        notif.add(
            Level.ERROR,
            f"Dependencia no instalada: {package}",
            f"No se pudo instalar automáticamente. Algunas funciones pueden no estar disponibles.",
            action_label="Reintentar instalación",
            action=_make_retry(package, mod),
        )


def main() -> None:
    db.init_db()
    first_run = not cfg.load()

    app = QApplication(sys.argv)
    app.setApplicationName("Gestión Red Doméstica")
    app.setOrganizationName("LeoNelastres")

    from gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    # Post any install failures now that the GUI is ready
    _post_pending_notifications()

    if first_run:
        from gui.setup_wizard import SetupWizard
        wizard = SetupWizard(window)
        wizard.exec()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
