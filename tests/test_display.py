"""Tests for display formatting functions."""

import pytest
from datetime import date, timedelta

from habit_tracker.display import (
    format_entries_table,
    format_streak,
    format_summary,
    format_table,
    format_week,
)


# ── format_table ──────────────────────────────────────────────────────────────

def test_format_table_basic():
    data = [{"name": "run", "date": "2025-01-01"}]
    result = format_table(data, ["name", "date"])
    assert "run" in result
    assert "2025-01-01" in result
    assert "NAME" in result


def test_format_table_empty():
    result = format_table([], ["name", "date"])
    assert "no data" in result


def test_format_table_multiple_rows():
    data = [
        {"habit": "run", "streak": "5"},
        {"habit": "swim", "streak": "3"},
    ]
    result = format_table(data, ["habit", "streak"])
    assert "run" in result
    assert "swim" in result
    assert "5" in result


# ── format_week ───────────────────────────────────────────────────────────────

def test_format_week_all_done():
    today = date.today()
    entries = [
        {"date": (today - timedelta(days=6 - i)).isoformat(), "value": "done"}
        for i in range(7)
    ]
    result = format_week("exercise", entries)
    assert "exercise" in result
    assert "✓" in result


def test_format_week_with_gaps():
    today = date.today()
    entries = []
    for i in range(7):
        d = (today - timedelta(days=6 - i)).isoformat()
        entries.append({"date": d, "value": "done" if i % 2 == 0 else None})
    result = format_week("run", entries)
    assert "✓" in result
    assert "·" in result


def test_format_week_all_missed():
    today = date.today()
    entries = [
        {"date": (today - timedelta(days=6 - i)).isoformat(), "value": None}
        for i in range(7)
    ]
    result = format_week("yoga", entries)
    assert "·" in result


# ── format_streak ─────────────────────────────────────────────────────────────

def test_format_streak_zero():
    result = format_streak("run", 0)
    assert "no streak" in result


def test_format_streak_single():
    result = format_streak("run", 1)
    assert "1 day" in result
    assert "🔥" not in result


def test_format_streak_plural():
    result = format_streak("run", 3)
    assert "3 days" in result


def test_format_streak_fire_at_7():
    result = format_streak("run", 7)
    assert "🔥" in result
    assert "7" in result


def test_format_streak_large():
    result = format_streak("run", 42)
    assert "42" in result
    assert "🔥" in result


# ── format_summary ────────────────────────────────────────────────────────────

def test_format_summary_no_habits():
    data = {"date": "2025-01-01", "habits": []}
    result = format_summary(data)
    assert "No habits" in result


def test_format_summary_with_habits():
    data = {
        "date": "2025-01-01",
        "habits": [
            {"name": "run", "description": "Morning run", "done_today": True, "value": "done", "streak": 5},
            {"name": "read", "description": "Read 30 min", "done_today": False, "value": None, "streak": 0},
        ],
    }
    result = format_summary(data)
    assert "run" in result
    assert "read" in result
    assert "1/2 done" in result


def test_format_summary_all_done():
    data = {
        "date": "2025-01-01",
        "habits": [
            {"name": "a", "description": "", "done_today": True, "value": "done", "streak": 1},
        ],
    }
    result = format_summary(data)
    assert "1/1 done" in result
    assert "✓" in result


# ── format_entries_table ──────────────────────────────────────────────────────

def test_format_entries_table_empty():
    result = format_entries_table("run", [])
    assert "No entries" in result


def test_format_entries_table_with_data():
    entries = [
        {"date": "2025-01-01", "value": "done", "notes": "felt great"},
        {"date": "2024-12-31", "value": "5km", "notes": ""},
    ]
    result = format_entries_table("run", entries)
    assert "2025-01-01" in result
    assert "done" in result
    assert "felt great" in result
    assert "5km" in result
