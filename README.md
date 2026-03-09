# habit-tracker-cli

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/RedBeret/habit-tracker-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/RedBeret/habit-tracker-cli/actions)

Track daily habits from your terminal — no phone app, no subscription, no cloud.
SQLite storage, streak tracking, and weekly sparklines. Works great with cron.

---

## Why

Most habit trackers are phone apps with accounts, sync requirements, and monthly fees.
This one runs in your shell, stores everything in a local SQLite file, and gets out of your way.

- **Private** — data stays on your machine
- **Scriptable** — cron it, pipe it, alias it
- **Fast** — sub-100ms for all commands
- **Zero cloud** — no accounts, no sync, no fees

---

## Install

```bash
pip install habit-tracker-cli
```

Or from source:

```bash
git clone https://github.com/RedBeret/habit-tracker-cli
cd habit-tracker-cli
pip install -e .
```

---

## Quick Start

```bash
# Initialize (creates ~/.habit-tracker/habits.db)
habit init

# Add habits
habit add exercise --description "Daily workout"
habit add reading  --description "Read for 30 min"
habit add water    --description "Drink 8 glasses"

# Log today's entries
habit log exercise "ran 3 miles"
habit log reading
habit log water "8 glasses" --notes "staying hydrated"

# See today's dashboard
habit view
```

**Dashboard output:**
```
  Habits — 2026-03-09

  exercise  ✓ done  ran 3 miles  5d
  reading   ✓ done              1d
  water     · pending

  2/3 done today
```

---

## All Commands

### `habit add <name>`
Add a new habit to track.
```bash
habit add meditation --description "10 min morning session"
```

### `habit log <name> [value]`
Log an entry. Value defaults to `done`. Accepts `--date` and `--notes`.
```bash
habit log exercise                           # logs "done" for today
habit log exercise "ran 5km"                 # custom value
habit log exercise --date yesterday          # log for yesterday
habit log exercise --date 2026-03-01         # log for specific date
habit log exercise "yoga" --notes "30 min"  # with notes
```

### `habit view [name]`
Without a name: shows today's dashboard. With a name: shows last 30 entries.
```bash
habit view           # dashboard
habit view exercise  # recent entries for "exercise"
```

### `habit week [name]`
7-day sparkline view. Shows all habits or one.
```bash
habit week
habit week exercise
```

**Output:**
```
  exercise
  Mo  Tu  We  Th  Fr  Sa  Su
  ✓   ✓   ✓   ·   ✓   ·   ✓
```

### `habit streak [name]`
Current consecutive-day streak.
```bash
habit streak            # all habits
habit streak exercise   # one habit
```

**Output:**
```
  exercise: 12 days 🔥
  reading: 3 days
  water: no streak
```

### `habit list`
List all configured habits.

### `habit remove <name>`
Deactivate a habit (entries are preserved).

### `habit export`
Export all data to CSV or JSON.
```bash
habit export --format csv > habits.csv
habit export --format json > habits.json
```

---

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--db PATH` | `~/.habit-tracker/habits.db` | Database location |
| `HABIT_DB` env var | same | Alternative to `--db` |

```bash
# Use a custom database
habit --db ~/work/habits.db view

# Or via environment variable
export HABIT_DB=~/work/habits.db
habit view
```

---

## Cron Integration

Log habits automatically or get a daily reminder:

```cron
# Log "done" for morning-routine every day at 9am
0 9 * * * habit log morning-routine

# Daily summary at 8pm
0 20 * * * habit view >> ~/habit-summary.txt
```

---

## Development

```bash
git clone https://github.com/RedBeret/habit-tracker-cli
cd habit-tracker-cli
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## License

MIT — see [LICENSE](LICENSE).
