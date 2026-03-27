# Workflow: Sync Hoopit Appointments to Supabase

## Objective
Fetch upcoming Hoopit appointments and upsert them into Supabase so the iPhone dashboard stays current.

## Required .env Variables

| Variable | Description |
|----------|-------------|
| `HOOPIT_PHONE` | Hoopit login phone number |
| `HOOPIT_PASSWORD` | Hoopit login password |
| `SUPABASE_URL` | `https://bpnjioorcjqvntxkpuia.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (secret) |

## Tool
`tools/send_hoopit_to_supabase.py`

## Run Manually
```bash
pip install -r requirements.txt
python tools/send_hoopit_to_supabase.py
```

## Architecture

```
Daily cron at 20:00 Oslo (18:00 UTC)
    → Remote Claude agent (trigger: trig_013ZfREnAXyXsHoytc4hjGCX)
    → python tools/send_hoopit_to_supabase.py
    → Hoopit API → Firebase auth → /app/users/current/events/
    → Upsert into Supabase table: hoopit_appointments
    → iPhone dashboard reads via anon key
```

## Supabase Table
Project: **WebTest** (`bpnjioorcjqvntxkpuia`)
Table: `hoopit_appointments`
Columns: `id`, `event_id`, `title`, `group_name`, `datetime`, `end_time`, `location`, `updated_at`
RLS: public read, service key required for writes

## iPhone Dashboard
URL: https://hoopit-dashboard-ogl90lc0m-oysteinvatland-droids-projects.vercel.app

To add to home screen: Safari → Share → Add to Home Screen

## Scheduled Trigger
- **ID:** `trig_013ZfREnAXyXsHoytc4hjGCX`
- **Schedule:** Daily at 18:00 UTC (20:00 Oslo summer / 19:00 Oslo winter)
- **Manage:** https://claude.ai/code/scheduled/trig_013ZfREnAXyXsHoytc4hjGCX

## Known Issues

### DST drift
The cron runs at 18:00 UTC. In winter (when Oslo is UTC+1) this fires at 19:00 Oslo instead of 20:00. Update the cron to `0 19 * * *` in winter if needed.

### Duplicate IDs
The Hoopit API sometimes returns the same event ID multiple times. The tool deduplicates before upserting.
