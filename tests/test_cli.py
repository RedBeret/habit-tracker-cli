"""Tests for the Click CLI commands."""

import json
import csv
import io
import pytest
from pathlib import Path

from click.testing import CliRunner

from habit_tracker.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.db")


def invoke(runner, db_path, *args):
    """Helper: invoke CLI with --db pointing to test db."""
    return runner.invoke(cli, ["--db", db_path] + list(args))


# ── init ──────────────────────────────────────────────────────────────────────

def test_init(runner, db_path):
    result = invoke(runner, db_path, "init")
    assert result.exit_code == 0
    assert "initialized" in result.output.lower()


# ── add ───────────────────────────────────────────────────────────────────────

def test_add_habit(runner, db_path):
    result = invoke(runner, db_path, "add", "exercise", "-d", "Daily workout")
    assert result.exit_code == 0
    assert "Added" in result.output


def test_add_duplicate_exits_nonzero(runner, db_path):
    invoke(runner, db_path, "add", "run")
    result = invoke(runner, db_path, "add", "run")
    assert result.exit_code != 0


# ── list ──────────────────────────────────────────────────────────────────────

def test_list_empty(runner, db_path):
    result = invoke(runner, db_path, "list")
    assert result.exit_code == 0
    assert "No habits" in result.output


def test_list_shows_habits(runner, db_path):
    invoke(runner, db_path, "add", "yoga")
    invoke(runner, db_path, "add", "reading")
    result = invoke(runner, db_path, "list")
    assert result.exit_code == 0
    assert "yoga" in result.output
    assert "reading" in result.output


# ── log ───────────────────────────────────────────────────────────────────────

def test_log_entry(runner, db_path):
    invoke(runner, db_path, "add", "water")
    result = invoke(runner, db_path, "log", "water", "8 glasses")
    assert result.exit_code == 0
    assert "Logged" in result.output


def test_log_with_date(runner, db_path):
    invoke(runner, db_path, "add", "run")
    result = invoke(runner, db_path, "log", "run", "5km", "--date", "2025-01-01")
    assert result.exit_code == 0


def test_log_unknown_habit_exits_nonzero(runner, db_path):
    result = invoke(runner, db_path, "log", "ghost")
    assert result.exit_code != 0


# ── view ──────────────────────────────────────────────────────────────────────

def test_view_dashboard_empty(runner, db_path):
    result = invoke(runner, db_path, "view")
    assert result.exit_code == 0
    assert "No habits" in result.output


def test_view_dashboard_with_habits(runner, db_path):
    invoke(runner, db_path, "add", "run")
    invoke(runner, db_path, "log", "run")
    result = invoke(runner, db_path, "view")
    assert result.exit_code == 0
    assert "run" in result.output


def test_view_specific_habit(runner, db_path):
    invoke(runner, db_path, "add", "yoga")
    invoke(runner, db_path, "log", "yoga", "30 min")
    result = invoke(runner, db_path, "view", "yoga")
    assert result.exit_code == 0
    assert "yoga" in result.output
    assert "30 min" in result.output


# ── week ──────────────────────────────────────────────────────────────────────

def test_week_no_habits(runner, db_path):
    result = invoke(runner, db_path, "week")
    assert result.exit_code == 0
    assert "No habits" in result.output


def test_week_all_habits(runner, db_path):
    invoke(runner, db_path, "add", "run")
    invoke(runner, db_path, "log", "run")
    result = invoke(runner, db_path, "week")
    assert result.exit_code == 0
    assert "run" in result.output


def test_week_specific_habit(runner, db_path):
    invoke(runner, db_path, "add", "yoga")
    result = invoke(runner, db_path, "week", "yoga")
    assert result.exit_code == 0
    assert "yoga" in result.output


# ── streak ────────────────────────────────────────────────────────────────────

def test_streak_no_habits(runner, db_path):
    result = invoke(runner, db_path, "streak")
    assert result.exit_code == 0
    assert "No habits" in result.output


def test_streak_shows_count(runner, db_path):
    invoke(runner, db_path, "add", "run")
    invoke(runner, db_path, "log", "run")
    result = invoke(runner, db_path, "streak")
    assert result.exit_code == 0
    assert "run" in result.output


# ── remove ────────────────────────────────────────────────────────────────────

def test_remove_habit(runner, db_path):
    invoke(runner, db_path, "add", "swim")
    result = invoke(runner, db_path, "remove", "swim", "--yes")
    assert result.exit_code == 0
    assert "Deactivated" in result.output


def test_remove_nonexistent(runner, db_path):
    result = invoke(runner, db_path, "remove", "ghost", "--yes")
    assert result.exit_code != 0


# ── export ────────────────────────────────────────────────────────────────────

def test_export_csv(runner, db_path):
    invoke(runner, db_path, "add", "run")
    invoke(runner, db_path, "log", "run", "5km", "--date", "2025-01-01")
    result = invoke(runner, db_path, "export", "--format", "csv")
    assert result.exit_code == 0
    reader = csv.DictReader(io.StringIO(result.output))
    rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["habit"] == "run"


def test_export_json(runner, db_path):
    invoke(runner, db_path, "add", "yoga")
    invoke(runner, db_path, "log", "yoga", "30 min", "--date", "2025-01-01")
    result = invoke(runner, db_path, "export", "--format", "json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["habit"] == "yoga"


def test_export_no_data(runner, db_path):
    result = invoke(runner, db_path, "export")
    assert result.exit_code == 0


# ── version ───────────────────────────────────────────────────────────────────

def test_version(runner, db_path):
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
