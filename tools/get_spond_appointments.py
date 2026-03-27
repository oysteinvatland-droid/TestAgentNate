"""
Retrieve the next 2 upcoming appointments from Spond.

Requirements:
    .env must contain SPOND_USERNAME and SPOND_PASSWORD
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from spond import spond

load_dotenv("/workspaces/TestAgentNate/.env")

SPOND_USERNAME = os.getenv("SPOND_USERNAME")
SPOND_PASSWORD = os.getenv("SPOND_PASSWORD")


def validate_env():
    missing = [k for k, v in {
        "SPOND_USERNAME": SPOND_USERNAME,
        "SPOND_PASSWORD": SPOND_PASSWORD,
    }.items() if not v]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)


def fmt_dt(ts):
    if not ts:
        return "", ""
    d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return d.strftime("%Y-%m-%d"), d.strftime("%H:%M")


async def main():
    s = spond.Spond(username=SPOND_USERNAME, password=SPOND_PASSWORD)
    try:
        events = await s.get_events(min_end=datetime.now(timezone.utc))
    finally:
        await s.clientsession.close()

    events = sorted(events, key=lambda e: e.get("startTimestamp", ""))
    next_two = events[:2]

    if not next_two:
        print("No upcoming Spond appointments found.")
        return

    print(f"\nNext {len(next_two)} upcoming Spond appointment(s):\n")
    for i, e in enumerate(next_two, 1):
        title      = e.get("heading") or "Untitled"
        group_name = (e.get("recipients") or {}).get("group", {}).get("name") or ""
        date, time = fmt_dt(e.get("startTimestamp"))
        _, end_t   = fmt_dt(e.get("endTimestamp"))
        location   = (e.get("location") or {}).get("feature", {}).get("description") or ""

        print(f"  {i}. {title}")
        if group_name:
            print(f"     Group: {group_name}")
        print(f"     Date:  {date}")
        if time:
            time_str = f"{time}–{end_t}" if end_t else time
            print(f"     Time:  {time_str}")
        if location:
            print(f"     Where: {location}")
        print()


if __name__ == "__main__":
    validate_env()
    asyncio.run(main())
