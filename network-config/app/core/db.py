import sqlite3
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path


DB_PATH = Path(__file__).parent.parent / "data" / "changes.db"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS change_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device TEXT NOT NULL,
                action TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                status TEXT DEFAULT 'ok',
                reversible INTEGER DEFAULT 0,
                revert_data TEXT
            )
        """)
        conn.commit()


def log_change(
    device: str,
    action: str,
    old_value: str | None,
    new_value: str | None,
    reversible: bool = False,
    revert_data: str | None = None,
    status: str = "ok",
) -> int:
    ts = datetime.now().isoformat(sep=" ", timespec="seconds")
    with _get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO change_log
                (timestamp, device, action, old_value, new_value, status, reversible, revert_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ts, device, action, old_value, new_value, status, int(reversible), revert_data),
        )
        conn.commit()
        return cur.lastrowid


def get_all(device_filter: str | None = None) -> list[sqlite3.Row]:
    with _get_connection() as conn:
        if device_filter:
            return conn.execute(
                "SELECT * FROM change_log WHERE device = ? ORDER BY id DESC",
                (device_filter,),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM change_log ORDER BY id DESC"
        ).fetchall()


def revert(entry_id: int) -> tuple[bool, str]:
    with _get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM change_log WHERE id = ?", (entry_id,)
        ).fetchone()
        if not row:
            return False, "Entrada no encontrada"
        if not row["reversible"]:
            return False, "Esta acción no es reversible"
        # Mark as reverted; actual revert logic is handled by caller using revert_data
        conn.execute(
            "UPDATE change_log SET status = 'revertido' WHERE id = ?", (entry_id,)
        )
        conn.commit()
        return True, row["revert_data"] or ""


def export_csv(path: str) -> tuple[bool, str]:
    try:
        rows = get_all()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["ID", "Fecha/Hora", "Dispositivo", "Acción", "Valor anterior", "Valor nuevo", "Estado"]
            )
            for r in rows:
                writer.writerow([
                    r["id"], r["timestamp"], r["device"], r["action"],
                    r["old_value"], r["new_value"], r["status"],
                ])
        return True, path
    except Exception as e:
        return False, str(e)


def cleanup_old(days: int = 30) -> int:
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(sep=" ", timespec="seconds")
    with _get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM change_log WHERE timestamp < ?", (cutoff,)
        )
        conn.commit()
        return cur.rowcount
