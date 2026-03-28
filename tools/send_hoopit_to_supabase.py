"""
Fetch upcoming Hoopit appointments and upsert them into Supabase.

Runs as part of the daily 20:00 scheduled trigger.

Requirements:
    .env must contain HOOPIT_PHONE, HOOPIT_PASSWORD,
    SUPABASE_URL, and SUPABASE_SERVICE_KEY
"""

import os
import sys
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Import auth + fetch from the existing Hoopit tool
sys.path.insert(0, os.path.dirname(__file__))
from get_hoopit_appointments import validate_env, get_firebase_token, get_appointments


def validate_supabase_env():
    missing = [k for k, v in {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY,
    }.items() if not v]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)


def upsert_appointments(events):
    seen = set()
    rows = []
    for e in events:
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        rows.append({
            "id":         e["id"],
            "event_id":   e.get("event_id"),
            "title":      e.get("title") or e.get("name") or "Untitled",
            "group_name": (e.get("group") or {}).get("name") or "",
            "datetime":   e.get("datetime") or e.get("start"),
            "end_time":   e.get("end"),
            "location":   e.get("location") or "",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/hoopit_appointments",
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
    validate_supabase_env()

    print("Fetching Hoopit appointments...")
    id_token = get_firebase_token()
    data = get_appointments(id_token)

    events = data if isinstance(data, list) else data.get("results", [])
    if not events:
        print("No upcoming appointments found.")
        sys.exit(0)

    count = upsert_appointments(events)
    print(f"Upserted {count} appointment(s) to Supabase.")
