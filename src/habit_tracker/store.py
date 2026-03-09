"""SQLite storage backend for habit tracker."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_DB_PATH = Path.home() / ".habit-tracker" / "habits.db"


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS habits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            description TEXT    DEFAULT '',
            created_at  TEXT    NOT NULL,
            active      INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS entries (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id   INTEGER NOT NULL REFERENCES habits(id),
            date       TEXT    NOT NULL,
            value      TEXT    DEFAULT 'done',
            notes      TEXT    DEFAULT '',
            created_at TEXT    NOT NULL,
            UNIQUE(habit_id, date)
        );
        """
    )
    conn.commit()


class HabitStore:
    """Low-level SQLite operations for habits and entries."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def open(self) -> "HabitStore":
        self._conn = _connect(self.db_path)
        _migrate(self._conn)
        return self

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "HabitStore":
        return self.open()

    def __exit__(self, *_) -> None:
        self.close()

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Store is not open — use 'with HabitStore() as store:'")
        return self._conn

    # ── habits ────────────────────────────────────────────────────────────────

    def add_habit(self, name: str, description: str = "") -> int:
        """Insert a new habit. Raises ValueError if name already exists."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            cur = self.conn.execute(
                "INSERT INTO habits (name, description, created_at) VALUES (?, ?, ?)",
                (name.lower().strip(), description, now),
            )
            self.conn.commit()
            return cur.lastrowid  # type: ignore[return-value]
        except sqlite3.IntegrityError:
            raise ValueError(f"Habit '{name}' already exists.")

    def get_habit(self, name: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM habits WHERE name = ? AND active = 1",
            (name.lower().strip(),),
        ).fetchone()
        return dict(row) if row else None

    def list_habits(self, active_only: bool = True) -> list[dict]:
        query = "SELECT * FROM habits"
        params: tuple = ()
        if active_only:
            query += " WHERE active = 1"
        rows = self.conn.execute(query + " ORDER BY name", params).fetchall()
        return [dict(r) for r in rows]

    def deactivate_habit(self, name: str) -> bool:
        cur = self.conn.execute(
            "UPDATE habits SET active = 0 WHERE name = ? AND active = 1",
            (name.lower().strip(),),
        )
        self.conn.commit()
        return cur.rowcount > 0

    # ── entries ───────────────────────────────────────────────────────────────

    def log_entry(
        self,
        habit_name: str,
        entry_date: str,
        value: str = "done",
        notes: str = "",
    ) -> None:
        """Insert or replace an entry for a habit on a given date."""
        habit = self.get_habit(habit_name)
        if habit is None:
            raise ValueError(f"Habit '{habit_name}' not found.")
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """INSERT INTO entries (habit_id, date, value, notes, created_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(habit_id, date) DO UPDATE SET value=excluded.value, notes=excluded.notes""",
            (habit["id"], entry_date, value, notes, now),
        )
        self.conn.commit()

    def get_entries(self, habit_name: str, days: int = 30) -> list[dict]:
        habit = self.get_habit(habit_name)
        if habit is None:
            return []
        rows = self.conn.execute(
            """SELECT e.date, e.value, e.notes
               FROM entries e
               WHERE e.habit_id = ?
               ORDER BY e.date DESC
               LIMIT ?""",
            (habit["id"], days),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_entry_for_date(self, habit_name: str, entry_date: str) -> Optional[dict]:
        habit = self.get_habit(habit_name)
        if habit is None:
            return None
        row = self.conn.execute(
            "SELECT * FROM entries WHERE habit_id = ? AND date = ?",
            (habit["id"], entry_date),
        ).fetchone()
        return dict(row) if row else None

    def get_all_today(self, today: Optional[str] = None) -> list[dict]:
        """Return all active habits with today's entry (if any)."""
        today_str = today or date.today().isoformat()
        rows = self.conn.execute(
            """SELECT h.name, h.description, e.value, e.notes
               FROM habits h
               LEFT JOIN entries e ON e.habit_id = h.id AND e.date = ?
               WHERE h.active = 1
               ORDER BY h.name""",
            (today_str,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_entries_for_range(
        self, habit_name: str, start_date: str, end_date: str
    ) -> list[dict]:
        habit = self.get_habit(habit_name)
        if habit is None:
            return []
        rows = self.conn.execute(
            """SELECT date, value, notes FROM entries
               WHERE habit_id = ? AND date BETWEEN ? AND ?
               ORDER BY date""",
            (habit["id"], start_date, end_date),
        ).fetchall()
        return [dict(r) for r in rows]

    def export_all(self) -> list[dict]:
        """Export everything for CSV/JSON dump."""
        rows = self.conn.execute(
            """SELECT h.name AS habit, e.date, e.value, e.notes, e.created_at
               FROM entries e
               JOIN habits h ON h.id = e.habit_id
               ORDER BY h.name, e.date"""
        ).fetchall()
        return [dict(r) for r in rows]
