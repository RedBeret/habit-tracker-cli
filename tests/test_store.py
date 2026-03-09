"""Tests for HabitStore — CRUD operations."""

import pytest
from pathlib import Path

from habit_tracker.store import HabitStore


@pytest.fixture
def store(tmp_path: Path):
    s = HabitStore(tmp_path / "test.db")
    s.open()
    yield s
    s.close()


# ── habits ────────────────────────────────────────────────────────────────────

def test_add_and_get_habit(store: HabitStore):
    store.add_habit("exercise", "Daily workout")
    h = store.get_habit("exercise")
    assert h is not None
    assert h["name"] == "exercise"
    assert h["description"] == "Daily workout"
    assert h["active"] == 1


def test_habit_name_is_lowercased(store: HabitStore):
    store.add_habit("Exercise")
    h = store.get_habit("exercise")
    assert h is not None


def test_add_duplicate_habit_raises(store: HabitStore):
    store.add_habit("reading")
    with pytest.raises(ValueError, match="already exists"):
        store.add_habit("reading")


def test_list_habits_empty(store: HabitStore):
    assert store.list_habits() == []


def test_list_habits_returns_active(store: HabitStore):
    store.add_habit("a")
    store.add_habit("b")
    habits = store.list_habits()
    assert len(habits) == 2
    assert {h["name"] for h in habits} == {"a", "b"}


def test_deactivate_habit(store: HabitStore):
    store.add_habit("swim")
    ok = store.deactivate_habit("swim")
    assert ok is True
    assert store.get_habit("swim") is None  # active=0 filtered out
    all_habits = store.list_habits(active_only=False)
    assert any(h["name"] == "swim" for h in all_habits)


def test_deactivate_nonexistent(store: HabitStore):
    ok = store.deactivate_habit("ghost")
    assert ok is False


# ── entries ───────────────────────────────────────────────────────────────────

def test_log_and_get_entry(store: HabitStore):
    store.add_habit("water")
    store.log_entry("water", "2025-01-01", "8 glasses")
    entries = store.get_entries("water")
    assert len(entries) == 1
    assert entries[0]["date"] == "2025-01-01"
    assert entries[0]["value"] == "8 glasses"


def test_log_entry_upsert(store: HabitStore):
    """Logging same day twice should update, not duplicate."""
    store.add_habit("sleep")
    store.log_entry("sleep", "2025-01-01", "7h")
    store.log_entry("sleep", "2025-01-01", "8h")
    entries = store.get_entries("sleep")
    assert len(entries) == 1
    assert entries[0]["value"] == "8h"


def test_log_entry_unknown_habit_raises(store: HabitStore):
    with pytest.raises(ValueError, match="not found"):
        store.log_entry("ghost", "2025-01-01")


def test_get_entry_for_date(store: HabitStore):
    store.add_habit("journal")
    store.log_entry("journal", "2025-03-01", "done", "Wrote 3 pages")
    entry = store.get_entry_for_date("journal", "2025-03-01")
    assert entry is not None
    assert entry["notes"] == "Wrote 3 pages"


def test_get_entries_limit(store: HabitStore):
    store.add_habit("run")
    for i in range(1, 40):
        store.log_entry("run", f"2025-01-{i:02d}", "done")
    entries = store.get_entries("run", days=10)
    assert len(entries) == 10


def test_get_all_today(store: HabitStore):
    store.add_habit("a")
    store.add_habit("b")
    store.log_entry("a", "2025-01-01", "done")
    today_data = store.get_all_today("2025-01-01")
    assert len(today_data) == 2
    a = next(x for x in today_data if x["name"] == "a")
    b = next(x for x in today_data if x["name"] == "b")
    assert a["value"] == "done"
    assert b["value"] is None


def test_get_entries_range(store: HabitStore):
    store.add_habit("yoga")
    store.log_entry("yoga", "2025-01-01")
    store.log_entry("yoga", "2025-01-03")
    store.log_entry("yoga", "2025-01-05")
    entries = store.get_all_entries_for_range("yoga", "2025-01-01", "2025-01-04")
    assert len(entries) == 2


def test_export_all(store: HabitStore):
    store.add_habit("meditation")
    store.log_entry("meditation", "2025-01-01", "20 min")
    data = store.export_all()
    assert len(data) == 1
    assert data[0]["habit"] == "meditation"
    assert data[0]["value"] == "20 min"


def test_context_manager(tmp_path: Path):
    with HabitStore(tmp_path / "ctx.db") as s:
        s.add_habit("test")
        assert s.get_habit("test") is not None


def test_conn_raises_when_not_open(tmp_path: Path):
    s = HabitStore(tmp_path / "closed.db")
    with pytest.raises(RuntimeError, match="not open"):
        _ = s.conn
