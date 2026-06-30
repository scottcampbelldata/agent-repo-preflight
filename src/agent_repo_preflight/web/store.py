from __future__ import annotations

import json
import secrets
import sqlite3
from typing import Protocol

_DDL = """CREATE TABLE IF NOT EXISTS scans (
  id TEXT PRIMARY KEY, source TEXT, name TEXT, verdict TEXT, score INTEGER,
  scanned_at TEXT, report_json TEXT, created_at TEXT)"""


class ScanStore(Protocol):
    def save(self, report_dict: dict, *, created_at: str) -> str: ...
    def get(self, id: str) -> dict | None: ...
    def list_recent(self, limit: int = 20) -> list[dict]: ...


class SqliteScanStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        with self._conn() as c:
            c.execute(_DDL)

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, report_dict: dict, *, created_at: str) -> str:
        sid = secrets.token_hex(8)
        repo = report_dict.get("repo", {})
        with self._conn() as c:
            c.execute(
                "INSERT INTO scans VALUES (?,?,?,?,?,?,?,?)",
                (
                    sid,
                    repo.get("source"),
                    repo.get("name"),
                    report_dict.get("verdict"),
                    report_dict.get("score"),
                    repo.get("scanned_at"),
                    json.dumps(report_dict),
                    created_at,
                ),
            )
        return sid

    def get(self, id: str) -> dict | None:
        with self._conn() as c:
            row = c.execute("SELECT report_json FROM scans WHERE id=?", (id,)).fetchone()
        return json.loads(row["report_json"]) if row else None

    def list_recent(self, limit: int = 20) -> list[dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, source, name, verdict, score, created_at FROM scans "
                "ORDER BY created_at DESC, rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
