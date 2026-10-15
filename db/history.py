import csv
import json
import sqlite3
import threading
from datetime import datetime

from utils.paths import data_dir

SCHEMA = """CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    app TEXT, category TEXT, raw_text TEXT, final_text TEXT, provider TEXT, duration REAL)"""
COLUMNS = ["id", "created_at", "app", "category", "raw_text", "final_text", "provider", "duration"]


class History:
    def __init__(self, path=None):
        self._conn = sqlite3.connect(str(path or data_dir() / "history.db"), check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(SCHEMA)
            self._conn.commit()

    def add(self, app, category, raw_text, final_text, provider, duration) -> int:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO history (created_at, app, category, raw_text, final_text, provider, duration) "
                "VALUES (?,?,?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), app, category, raw_text, final_text, provider, duration))
            self._conn.commit()
            return cur.lastrowid

    def search(self, query: str = "", limit: int = 500) -> list[dict]:
        sql, args = f"SELECT {','.join(COLUMNS)} FROM history", []
        if query:
            sql += " WHERE final_text LIKE ? OR raw_text LIKE ? OR app LIKE ?"
            args = [f"%{query}%"] * 3
        sql += " ORDER BY id DESC LIMIT ?"
        with self._lock:
            rows = self._conn.execute(sql, args + [limit]).fetchall()
        return [dict(zip(COLUMNS, r)) for r in rows]

    def delete(self, entry_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM history WHERE id=?", (entry_id,))
            self._conn.commit()

    def clear(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM history")
            self._conn.commit()

    def export(self, path: str, rows: list[dict] | None = None) -> None:
        rows = self.search(limit=1_000_000) if rows is None else rows
        if path.lower().endswith(".json"):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)
        elif path.lower().endswith(".csv"):
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=COLUMNS)
                w.writeheader()
                w.writerows(rows)
        else:
            with open(path, "w", encoding="utf-8") as f:
                for r in rows:
                    f.write(f"[{r['created_at']}] ({r['app']})\n{r['final_text']}\n\n")
