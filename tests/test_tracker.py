"""Tests for Tracker — streak calculation, date parsing, week fill."""

import pytest
from datetime import date, timedelta
from pathlib import Path

from habit_tracker.tracker import Tracker, _parse_date


# ── date parsing ──────────────────────────────────────────────────────────────

def test_parse_today():
    result = _parse_date("today")
    assert result == date.today().isoformat()


def test_parse_yesterday():
    result = _parse_date("yesterday")
    assert result == (date.today() - timedelta(days=1)).isoformat()


def test_parse_iso_date():
    assert _parse_date("2025-06-15") == "2025-06-15"


def test_parse_empty_string():
    assert _parse_date("") == date.today().isoformat()


def test_parse_invalid_date():
    with pytest.raises(ValueError):
        _parse_date("not-a-date")


# ── tracker fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def tracker(tmp_path: Path):
    t = Tracker(tmp_path / "test.db")
    t.open()
    yield t
    t.close()


# ── add / list / remove ───────────────────────────────────────────────────────

def test_add_habit(tracker: Tracker):
    tracker.add_habit("run", "Morning run")
    habits = tracker.list_habits()
    assert len(habits) == 1
    assert habits[0]["name"] == "run"


def test_add_empty_name_raises(tracker: Tracker):
    with pytest.raises(ValueError, match="empty"):
        tracker.add_habit("")


def test_add_long_name_raises(tracker: Tracker):
    with pytest.raises(ValueError, match="too long"):
        tracker.add_habit("x" * 51)


def test_remove_habit(tracker: Tracker):
    tracker.add_habit("swim")
    ok = tracker.remove_habit("swim")
    assert ok is True
    assert tracker.list_habits() == []


def test_remove_nonexistent(tracker: Tracker):
    assert tracker.remove_habit("ghost") is False


# ── logging ───────────────────────────────────────────────────────────────────

def test_log_today(tracker: Tracker):
    tracker.add_habit("water")
    tracker.log("water", "8 glasses")
    entries = tracker.get_recent("water", days=5)
    assert len(entries) == 1
    assert entries[0]["value"] == "8 glasses"


def test_log_specific_date(tracker: Tracker):
    tracker.add_habit("yoga")
    tracker.log("yoga", date_str="2025-01-15")
    entries = tracker.get_recent("yoga", days=400)
    assert any(e["date"] == "2025-01-15" for e in entries)


def test_log_unknown_habit_raises(tracker: Tracker):
    with pytest.raises(ValueError):
        tracker.log("ghost")


# ── streak calculation ────────────────────────────────────────────────────────

def test_streak_empty(tracker: Tracker):
    tracker.add_habit("run")
    assert tracker.get_streak("run") == 0


def test_streak_single_day_today(tracker: Tracker):
    tracker.add_habit("run")
    tracker.log("run", date_str="today")
    assert tracker.get_streak("run") == 1


def test_streak_consecutive_days(tracker: Tracker):
    tracker.add_habit("run")
    today = date.today()
    for i in range(5):
        d = (today - timedelta(days=i)).isoformat()
        tracker.store.log_entry("run", d)
    assert tracker.get_streak("run") == 5


def test_streak_with_gap(tracker: Tracker):
    tracker.add_habit("run")
    today = date.today()
    # Log today and yesterday but not 3 days ago
    tracker.store.log_entry("run", today.isoformat())
    tracker.store.log_entry("run", (today - timedelta(days=1)).isoformat())
    # Gap at day 2
    tracker.store.log_entry("run", (today - timedelta(days=3)).isoformat())
    assert tracker.get_streak("run") == 2


def test_streak_only_yesterday(tracker: Tracker):
    """If today not logged, streak counts from yesterday backward."""
    tracker.add_habit("run")
    today = date.today()
    tracker.store.log_entry("run", (today - timedelta(days=1)).isoformat())
    tracker.store.log_entry("run", (today - timedelta(days=2)).isoformat())
    assert tracker.get_streak("run") == 2


def test_streak_nonexistent_habit(tracker: Tracker):
    assert tracker.get_streak("ghost") == 0


# ── week view ─────────────────────────────────────────────────────────────────

def test_get_week_returns_7_days(tracker: Tracker):
    tracker.add_habit("yoga")
    entries = tracker.get_week("yoga")
    assert len(entries) == 7


def test_get_week_fills_missing_days(tracker: Tracker):
    tracker.add_habit("yoga")
    today = date.today()
    tracker.store.log_entry("yoga", today.isoformat())
    entries = tracker.get_week("yoga")
    assert len(entries) == 7
    # Only today has a value
    done = [e for e in entries if e.get("value") is not None]
    assert len(done) == 1


def test_get_week_with_custom_end_date(tracker: Tracker):
    tracker.add_habit("journal")
    end = date(2025, 3, 7)
    tracker.store.log_entry("journal", "2025-03-05")
    entries = tracker.get_week("journal", end_date=end)
    assert entries[0]["date"] == "2025-03-01"
    assert entries[-1]["date"] == "2025-03-07"


# ── summary ───────────────────────────────────────────────────────────────────

def test_summary_empty(tracker: Tracker):
    result = tracker.get_summary()
    assert result["habits"] == []


def test_summary_with_habits(tracker: Tracker):
    tracker.add_habit("a")
    tracker.add_habit("b")
    tracker.log("a")
    result = tracker.get_summary()
    assert len(result["habits"]) == 2
    a = next(h for h in result["habits"] if h["name"] == "a")
    b = next(h for h in result["habits"] if h["name"] == "b")
    assert a["done_today"] is True
    assert b["done_today"] is False


# ── export ────────────────────────────────────────────────────────────────────

def test_export_returns_data(tracker: Tracker):
    tracker.add_habit("sleep")
    tracker.log("sleep", "7h")
    data = tracker.export()
    assert len(data) == 1
    assert data[0]["habit"] == "sleep"
