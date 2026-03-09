"""Terminal formatting — tables, sparklines, colors."""

from __future__ import annotations

import os

# ── ANSI color helpers ────────────────────────────────────────────────────────

_COLORS_ENABLED = os.isatty(1)  # only colorize when connected to a terminal


def _color(code: str, text: str) -> str:
    if not _COLORS_ENABLED:
        return text
    return f"\033[{code}m{text}\033[0m"


def green(text: str) -> str:
    return _color("32", text)


def yellow(text: str) -> str:
    return _color("33", text)


def dim(text: str) -> str:
    return _color("2", text)


def bold(text: str) -> str:
    return _color("1", text)


def cyan(text: str) -> str:
    return _color("36", text)


# ── table formatting ──────────────────────────────────────────────────────────


def format_table(data: list[dict], headers: list[str]) -> str:
    """Render a list of dicts as a fixed-width ASCII table."""
    if not data:
        return dim("  (no data)")

    rows: list[list[str]] = []
    for row in data:
        rows.append([str(row.get(h, "")) for h in headers])

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    sep = "  ".join("-" * w for w in col_widths)
    header_line = "  ".join(h.upper().ljust(col_widths[i]) for i, h in enumerate(headers))

    lines = [bold(header_line), sep]
    for row in rows:
        line = "  ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
        lines.append(line)
    return "\n".join(lines)


# ── sparkline / week view ─────────────────────────────────────────────────────

_CHECK = "✓"
_MISS = "·"


def format_week(habit: str, entries: list[dict]) -> str:
    """7-day sparkline view. entries is a list of dicts with 'date' and 'value'."""
    from datetime import date, timedelta

    today = date.today()
    days_labels = []
    marks = []

    for entry in entries:
        d = date.fromisoformat(entry["date"])
        label = d.strftime("%a")[:2]
        days_labels.append(label)
        if entry.get("value") is not None:
            marks.append(green(_CHECK))
        else:
            marks.append(dim(_MISS))

    header = "  ".join(dim(l) for l in days_labels)
    bar = "  ".join(marks)
    return f"  {habit}\n  {header}\n  {bar}"


def format_streak(habit: str, count: int) -> str:
    """Format streak count with flame for 7+ day streaks."""
    if count == 0:
        return f"  {dim(habit)}: {dim('no streak')}"
    fire = " 🔥" if count >= 7 else ""
    color_fn = green if count >= 7 else yellow
    return f"  {bold(habit)}: {color_fn(str(count))} day{'s' if count != 1 else ''}{fire}"


def format_summary(data: dict) -> str:
    """Dashboard view showing all habits and today's status."""
    date_str = data.get("date", "")
    habits = data.get("habits", [])

    lines = [bold(f"\n  Habits — {date_str}"), ""]
    if not habits:
        lines.append(dim("  No habits yet. Run: habit add <name>"))
        return "\n".join(lines)

    name_w = max(len(h["name"]) for h in habits)

    for h in habits:
        name = h["name"].ljust(name_w)
        streak = h["streak"]

        if h["done_today"]:
            status = green(f"{_CHECK} done")
            val = h.get("value", "done")
            if val and val != "done":
                status += f"  {dim(val)}"
        else:
            status = dim(f"{_MISS} pending")

        streak_str = ""
        if streak > 0:
            fire = "🔥" if streak >= 7 else ""
            streak_str = yellow(f"  {streak}d{fire}")

        lines.append(f"  {bold(name)}  {status}{streak_str}")

    done_count = sum(1 for h in habits if h["done_today"])
    total = len(habits)
    lines.append("")
    lines.append(
        f"  {done_count}/{total} done today"
        + (" ✓" if done_count == total and total > 0 else "")
    )
    return "\n".join(lines)


def format_entries_table(habit: str, entries: list[dict]) -> str:
    """Format recent entries for `habit view <name>`."""
    if not entries:
        return dim(f"  No entries for '{habit}' yet.")
    lines = [bold(f"\n  {habit} — recent entries"), ""]
    for e in entries:
        val = e.get("value") or "done"
        notes = e.get("notes") or ""
        note_str = f"  {dim(notes)}" if notes else ""
        lines.append(f"  {cyan(e['date'])}  {green(val)}{note_str}")
    return "\n".join(lines)
