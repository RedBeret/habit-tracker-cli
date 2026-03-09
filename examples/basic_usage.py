#!/usr/bin/env python3
"""Basic usage example for habit-tracker-cli.

Run from the repo root:
    python examples/basic_usage.py
"""

import tempfile
from pathlib import Path
from datetime import date, timedelta

from habit_tracker.tracker import Tracker
from habit_tracker.display import format_summary, format_week, format_streak


def main():
    # Use a temp DB so this example is self-contained
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "habits.db"

        with Tracker(db_path) as t:
            # Add some habits
            t.add_habit("exercise", "Daily workout")
            t.add_habit("reading", "Read for 30 min")
            t.add_habit("water", "Drink 8 glasses")

            # Log entries for the past week
            today = date.today()
            exercise_days = [0, 1, 2, 4, 5, 6]  # skipped day 3
            reading_days = [0, 1, 2, 3, 4]       # 5 consecutive days
            water_days = [0]                       # only today

            for d in exercise_days:
                entry_date = (today - timedelta(days=d)).isoformat()
                t.store.log_entry("exercise", entry_date, "done")

            for d in reading_days:
                entry_date = (today - timedelta(days=d)).isoformat()
                t.store.log_entry("reading", entry_date, "30 min")

            for d in water_days:
                entry_date = (today - timedelta(days=d)).isoformat()
                t.store.log_entry("water", entry_date, "8 glasses")

            # Show today's dashboard
            print("\n=== Dashboard ===")
            summary = t.get_summary()
            print(format_summary(summary))

            # Show weekly sparklines
            print("\n=== Weekly View ===")
            for habit_name in ["exercise", "reading", "water"]:
                entries = t.get_week(habit_name)
                print(format_week(habit_name, entries))
                print()

            # Show streaks
            print("=== Streaks ===")
            for habit_name in ["exercise", "reading", "water"]:
                count = t.get_streak(habit_name)
                print(format_streak(habit_name, count))
            print()

            # Export data
            print("=== Export (first 3 entries) ===")
            data = t.export()
            for row in data[:3]:
                print(f"  {row['habit']} | {row['date']} | {row['value']}")


if __name__ == "__main__":
    main()
