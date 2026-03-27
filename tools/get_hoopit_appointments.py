"""
Retrieve the next 2 upcoming appointments from Hoopit.

Auth flow:
  1. POST credentials to api.hoopit.io/auth/ (Django) → gets Firebase custom token
  2. Exchange custom token for Firebase ID token via Google Identity Toolkit
  3. Use ID token as Bearer header against api.hoopit.io/app/users/current/events/

Requirements:
    .env must contain HOOPIT_PHONE and HOOPIT_PASSWORD
"""

import os
import sys
import re

import requests
from dotenv import load_dotenv

load_dotenv("/workspaces/TestAgentNate/.env")

HOOPIT_PHONE    = os.getenv("HOOPIT_PHONE")
HOOPIT_PASSWORD = os.getenv("HOOPIT_PASSWORD")
BASE_URL        = "https://api.hoopit.io"
FIREBASE_API_KEY = "AIzaSyBs2V8ZQQvQArdCPzNUiJ-nSR4x0e5G230"


def validate_env():
    missing = [k for k, v in {
        "HOOPIT_PHONE": HOOPIT_PHONE,
        "HOOPIT_PASSWORD": HOOPIT_PASSWORD,
    }.items() if not v]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)


def get_firebase_token():
    # Step 1: GET login page to obtain CSRF token
    session = requests.Session()
    r = session.get(f"{BASE_URL}/auth", timeout=15)
    r.raise_for_status()

    match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', r.text)
    if not match:
        print("ERROR: Could not find CSRF token on login page.")
        sys.exit(1)
    csrf = match.group(1)

    # Step 2: POST credentials — Django redirects to app.hoopit.io/?token=<custom_token>
    resp = session.post(
        f"{BASE_URL}/auth/",
        data={
            "csrfmiddlewaretoken": csrf,
            "phone_number": HOOPIT_PHONE,
            "password": HOOPIT_PASSWORD,
        },
        headers={"Referer": f"{BASE_URL}/auth"},
        timeout=15,
        allow_redirects=True,
    )

    match = re.search(r'[?&]token=([^&\s]+)', resp.url)
    if not match:
        print("ERROR: Login failed — no token in redirect URL. Check HOOPIT_PHONE and HOOPIT_PASSWORD.")
        sys.exit(1)
    custom_token = match.group(1)

    # Step 3: Exchange Firebase custom token for an ID token
    exchange = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={FIREBASE_API_KEY}",
        json={"token": custom_token, "returnSecureToken": True},
        timeout=15,
    )
    exchange.raise_for_status()
    return exchange.json()["idToken"]


def get_appointments(id_token):
    resp = requests.get(
        f"{BASE_URL}/app/users/current/events/",
        params={"page": 1, "pagination_count": "false"},
        headers={
            "Authorization": f"Bearer {id_token}",
            "Accept": "application/json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def print_appointments(data):
    # Handle list or dict with results key
    if isinstance(data, list):
        events = data
    elif isinstance(data, dict):
        events = data.get("results", data.get("events", data.get("data", [])))
    else:
        print("Unexpected response format. Raw response:")
        print(str(data)[:1000])
        return

    if not events:
        print("No upcoming appointments found.")
        return

    next_two = events[:2]
    print(f"\nNext {len(next_two)} upcoming appointment(s):\n")
    for i, appt in enumerate(next_two, 1):
        title    = appt.get("title") or appt.get("name") or "Untitled"
        dt       = appt.get("datetime") or appt.get("start") or appt.get("start_date") or ""
        end      = appt.get("end") or ""
        location = appt.get("location") or appt.get("venue") or ""
        group    = (appt.get("group") or {}).get("name") or ""

        # Format datetime: "2026-03-27T15:00:00+01:00" → "2026-03-27 15:00"
        if "T" in dt:
            date_part, time_part = dt[:10], dt[11:16]
        else:
            date_part, time_part = dt, ""
        if end and "T" in end:
            end_time = end[11:16]
        else:
            end_time = ""

        print(f"  {i}. {title}")
        if group:
            print(f"     Group: {group}")
        print(f"     Date:  {date_part}")
        if time_part:
            time_str = f"{time_part}–{end_time}" if end_time else time_part
            print(f"     Time:  {time_str}")
        if location:
            print(f"     Where: {location}")
        print()


if __name__ == "__main__":
    validate_env()
    id_token = get_firebase_token()
    data = get_appointments(id_token)
    print_appointments(data)
