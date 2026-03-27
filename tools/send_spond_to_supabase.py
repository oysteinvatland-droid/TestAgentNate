"""
Fetch upcoming Spond appointments and upsert them into Supabase.

Runs as part of the daily 20:00 scheduled trigger.

Requirements:
    .env must contain SPOND_USERNAME, SPOND_PASSWORD,
    SUPABASE_URL, and SUPABASE_SERVICE_KEY
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from spond import spond

load_dotenv("/workspaces/TestAgentNate/.env")

SPOND_USERNAME       = os.getenv("SPOND_USERNAME")
SPOND_PASSWORD       = os.getenv("SPOND_PASSWORD")
SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


def validate_env():
    missing = [k for k, v in {
        "SPOND_USERNAME":       SPOND_USERNAME,
        "SPOND_PASSWORD":       SPOND_PASSWORD,
        "SUPABASE_URL":         SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY,
    }.items() if not v]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)


async def fetch_events():
    s = spond.Spond(username=SPOND_USERNAME, password=SPOND_PASSWORD)
    try:
        return await s.get_events(min_end=datetime.now(timezone.utc))
    finally:
        await s.clientsession.close()


def upsert_appointments(events):
    rows = []
    for e in events:
        rows.append({
            "id":         e["id"],
            "title":      e.get("heading") or "Untitled",
            "group_name": (e.get("recipients") or {}).get("group", {}).get("name") or "",
            "datetime":   e.get("startTimestamp"),
            "end_time":   e.get("endTimestamp"),
            "location":   (e.get("location") or {}).get("feature", {}).get("description") or "",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/spond_appointments",
        headers={
            "apikey":        SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type":  "application/json",
            "Prefer":        "resolution=merge-duplicates",
        },
        json=rows,
        timeout=15,
    )
    if not resp.ok:
        print(f"ERROR {resp.status_code}: {resp.text[:500]}")
        resp.raise_for_status()
    return len(rows)


if __name__ == "__main__":
    validate_env()
    print("Fetching Spond appointments...")
    events = asyncio.run(fetch_events())
    if not events:
        print("No upcoming appointments found.")
        sys.exit(0)
    count = upsert_appointments(events)
    print(f"Upserted {count} appointment(s) to Supabase.")
