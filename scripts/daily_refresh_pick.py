"""Pick today's batch of listicles for the daily refresh agent.

Reads `data/refresh-state.json`, returns the next 10 slugs in publish-date
order starting at the cursor, then advances the cursor (mod 22).

Usage:
  python3 scripts/daily_refresh_pick.py            # prints today's 10 + advances cursor
  python3 scripts/daily_refresh_pick.py --peek     # prints today's 10 WITHOUT advancing
  python3 scripts/daily_refresh_pick.py --reset    # set cursor back to 0
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "data" / "refresh-state.json"
BATCH_SIZE = 6


def load() -> dict:
    return json.loads(STATE_FILE.read_text())


def save(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def pick(state: dict) -> list[str]:
    order = state["publish_order"]
    n = len(order)
    cursor = state["cursor"] % n
    # Take the next BATCH_SIZE, wrapping around.
    batch = [order[(cursor + i) % n] for i in range(BATCH_SIZE)]
    return batch


def advance(state: dict) -> None:
    n = len(state["publish_order"])
    state["cursor"] = (state["cursor"] + BATCH_SIZE) % n
    state["last_run"] = date.today().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--peek", action="store_true", help="Show today's batch without advancing the cursor")
    parser.add_argument("--reset", action="store_true", help="Reset cursor to 0 and exit")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of one slug per line")
    args = parser.parse_args()

    state = load()

    if args.reset:
        state["cursor"] = 0
        state["last_run"] = None
        save(state)
        print("cursor reset to 0")
        return 0

    batch = pick(state)

    if not args.peek:
        advance(state)
        save(state)

    if args.json:
        print(json.dumps({"date": date.today().isoformat(), "batch": batch, "cursor_after": state["cursor"]}))
    else:
        for slug in batch:
            print(slug)

    return 0


if __name__ == "__main__":
    sys.exit(main())
