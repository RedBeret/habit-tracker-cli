"""Business logic layer — validation, streak calculation, date handling."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from .store import DEFAULT_DB_PATH, HabitStore


def _parse_date(value: str) -> str:
    """Parse date string. Accepts 'today', 'yesterday', or YYYY-MM-DD."""
    v = value.strip().lower()
    if v in ("today", ""):
        return date.today().isoformat()
    if v == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    # Validate format
    parsed = date.fromisoformat(v)  # raises ValueError on bad format
    return parsed.isoformat()


class Tracker:
    """High-level habit tracker wrapping HabitStore."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.store = HabitStore(db_path)

    def open(self) -> "Tracker":
        self.store.open()
        return self

    def close(self) -> None:
        self.store.close()

    def __enter__(self) -> "Tracker":
        return self.open()

    def __exit__(self, *_) -> None:
        self.close()

    # ── habits ────────────────────────────────────────────────────────────────

    def add_habit(self, name: str, description: str = "") -> None:
        name = name.strip()
        if not name:
            raise ValueError("Habit name cannot be empty.")
        if len(name) > 50:
            raise ValueError("Habit name too long (max 50 chars).")
        self.store.add_habit(name, description)

    def list_habits(self) -> list[dict]:
        return self.store.list_habits()

    def remove_habit(self, name: str) -> bool:
        return self.store.deactivate_habit(name)

    # ── logging ───────────────────────────────────────────────────────────────

    def log(
        self,
        habit: str,
        value: str = "done",
        date_str: str = "today",
        notes: str = "",
    ) -> None:
        parsed = _parse_date(date_str)
        self.store.log_entry(habit, parsed, value, notes)

    # ── views ─────────────────────────────────────────────────────────────────

    def get_recent(self, habit: str, days: int = 14) -> list[dict]:
        return self.store.get_entries(habit, days)

    def get_week(self, habit: str, end_date: Optional[date] = None) -> list[dict]:
        """Last 7 days with None fill for missing entries."""
        end = end_date or date.today()
        start = end - timedelta(days=6)
        existing = {
            e["date"]: e
            for e in self.store.get_all_entries_for_range(
                habit, start.isoformat(), end.isoformat()
            )
        }
        result = []
        for i in range(7):
            d = (start + timedelta(days=i)).isoformat()
            result.append(existing.get(d) or {"date": d, "value": None, "notes": ""})
        return result

    def get_streak(self, habit: str) -> int:
        """Count consecutive days ending today (or yesterday if today not logged)."""
        entries = self.store.get_entries(habit, days=400)
        if not entries:
            return 0
        entry_dates = {e["date"] for e in entries}
        today = date.today()
        # Start from today; if today not logged, start from yesterday
        start = today if today.isoformat() in entry_dates else today - timedelta(days=1)
        streak = 0
        current = start
        while current.isoformat() in entry_dates:
            streak += 1
            current -= timedelta(days=1)
        return streak

    def get_summary(self, today: Optional[str] = None) -> dict:
        """Dashboard summary — all habits, today's status, streaks."""
        today_str = today or date.today().isoformat()
        today_entries = self.store.get_all_today(today_str)
        result = []
        for row in today_entries:
            streak = self.get_streak(row["name"])
            result.append(
                {
                    "name": row["name"],
                    "description": row["description"],
                    "done_today": row["value"] is not None,
                    "value": row["value"],
                    "streak": streak,
                }
            )
        return {"date": today_str, "habits": result}

    # ── export ────────────────────────────────────────────────────────────────

    def export(self) -> list[dict]:
        return self.store.export_all()
