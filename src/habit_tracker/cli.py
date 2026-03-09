"""Click CLI entry point for habit-tracker."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import click

from . import __version__
from .display import (
    format_entries_table,
    format_streak,
    format_summary,
    format_table,
    format_week,
)
from .store import DEFAULT_DB_PATH
from .tracker import Tracker

pass_tracker = click.make_pass_decorator(Tracker, ensure=True)


def _get_db_path(ctx_obj: dict) -> Path:
    return ctx_obj.get("db_path", DEFAULT_DB_PATH) if ctx_obj else DEFAULT_DB_PATH


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version")
@click.option(
    "--db",
    default=str(DEFAULT_DB_PATH),
    show_default=True,
    envvar="HABIT_DB",
    help="Path to the SQLite database.",
)
@click.pass_context
def cli(ctx: click.Context, db: str) -> None:
    """Terminal habit tracker — track daily habits from your shell."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = Path(db)


# ── init ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize the database and optionally add starter habits."""
    db_path = ctx.obj["db_path"]
    with Tracker(db_path):
        pass  # migrations run on open
    click.echo(f"  ✓ Database initialized at {db_path}")
    click.echo("")
    click.echo("  Add your first habits:")
    click.echo("    habit add exercise --description 'Daily workout'")
    click.echo("    habit add reading  --description 'Read for 30 min'")
    click.echo("    habit add water    --description 'Drink 8 glasses'")
    click.echo("")
    click.echo("  Then log them:")
    click.echo("    habit log exercise 'ran 3 miles'")
    click.echo("    habit log reading")
    click.echo("")
    click.echo("  See your dashboard:")
    click.echo("    habit view")


# ── add ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.option("-d", "--description", default="", help="Short description of the habit.")
@click.pass_context
def add(ctx: click.Context, name: str, description: str) -> None:
    """Add a new habit to track."""
    db_path = ctx.obj["db_path"]
    try:
        with Tracker(db_path) as t:
            t.add_habit(name, description)
        click.echo(f"  ✓ Added habit '{name}'")
    except ValueError as e:
        click.echo(f"  ✗ {e}", err=True)
        sys.exit(1)


# ── log ───────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.argument("value", default="done")
@click.option(
    "--date",
    "date_str",
    default="today",
    show_default=True,
    help="Date (YYYY-MM-DD, 'today', or 'yesterday').",
)
@click.option("-n", "--notes", default="", help="Optional notes for this entry.")
@click.pass_context
def log(ctx: click.Context, name: str, value: str, date_str: str, notes: str) -> None:
    """Log an entry for a habit. VALUE defaults to 'done'."""
    db_path = ctx.obj["db_path"]
    try:
        with Tracker(db_path) as t:
            t.log(name, value, date_str, notes)
        click.echo(f"  ✓ Logged '{name}' for {date_str}")
    except ValueError as e:
        click.echo(f"  ✗ {e}", err=True)
        sys.exit(1)


# ── view ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name", required=False)
@click.pass_context
def view(ctx: click.Context, name: str | None) -> None:
    """Show recent entries. Without NAME shows today's dashboard."""
    db_path = ctx.obj["db_path"]
    with Tracker(db_path) as t:
        if name:
            entries = t.get_recent(name, days=30)
            click.echo(format_entries_table(name, entries))
        else:
            summary = t.get_summary()
            click.echo(format_summary(summary))
    click.echo()


# ── week ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name", required=False)
@click.pass_context
def week(ctx: click.Context, name: str | None) -> None:
    """Show 7-day sparkline for one or all habits."""
    db_path = ctx.obj["db_path"]
    with Tracker(db_path) as t:
        habits = [name] if name else [h["name"] for h in t.list_habits()]
        if not habits:
            click.echo("  No habits yet. Run: habit add <name>")
            return
        click.echo()
        for h in habits:
            entries = t.get_week(h)
            click.echo(format_week(h, entries))
            click.echo()


# ── streak ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name", required=False)
@click.pass_context
def streak(ctx: click.Context, name: str | None) -> None:
    """Show current streak(s)."""
    db_path = ctx.obj["db_path"]
    with Tracker(db_path) as t:
        habits = [name] if name else [h["name"] for h in t.list_habits()]
        if not habits:
            click.echo("  No habits yet.")
            return
        click.echo()
        for h in habits:
            count = t.get_streak(h)
            click.echo(format_streak(h, count))
    click.echo()


# ── list ──────────────────────────────────────────────────────────────────────

@cli.command(name="list")
@click.pass_context
def list_habits(ctx: click.Context) -> None:
    """List all configured habits."""
    db_path = ctx.obj["db_path"]
    with Tracker(db_path) as t:
        habits = t.list_habits()
    if not habits:
        click.echo("  No habits yet. Run: habit add <name>")
        return
    click.echo()
    click.echo(
        format_table(
            habits,
            ["name", "description", "created_at"],
        )
    )
    click.echo()


# ── remove ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to deactivate this habit?")
@click.pass_context
def remove(ctx: click.Context, name: str) -> None:
    """Deactivate a habit (entries are kept)."""
    db_path = ctx.obj["db_path"]
    with Tracker(db_path) as t:
        ok = t.remove_habit(name)
    if ok:
        click.echo(f"  ✓ Deactivated habit '{name}'")
    else:
        click.echo(f"  ✗ Habit '{name}' not found.", err=True)
        sys.exit(1)


# ── export ────────────────────────────────────────────────────────────────────

@cli.command()
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["csv", "json"]),
    default="csv",
    show_default=True,
    help="Output format.",
)
@click.option("-o", "--output", default="-", help="Output file (default: stdout).")
@click.pass_context
def export(ctx: click.Context, fmt: str, output: str) -> None:
    """Export all habit data to CSV or JSON."""
    db_path = ctx.obj["db_path"]
    with Tracker(db_path) as t:
        data = t.export()

    if not data:
        click.echo("  No data to export.", err=True)
        return

    out = open(output, "w", newline="") if output != "-" else sys.stdout

    try:
        if fmt == "json":
            json.dump(data, out, indent=2)
            if output != "-":
                click.echo(f"  ✓ Exported {len(data)} entries to {output}")
        else:
            if data:
                writer = csv.DictWriter(out, fieldnames=list(data[0].keys()))
                writer.writeheader()
                writer.writerows(data)
            if output != "-":
                click.echo(f"  ✓ Exported {len(data)} entries to {output}")
    finally:
        if output != "-":
            out.close()


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
