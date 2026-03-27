# Workflow: Get Next 2 Hoopit Appointments

## Objective
Retrieve the two next upcoming appointments from Hoopit and print them to the terminal.

## Required Inputs
These must be set in `.env` before running:

| Variable | Description |
|----------|-------------|
| `HOOPIT_PHONE` | Hoopit login phone number (e.g. `90547746`) |
| `HOOPIT_PASSWORD` | Hoopit login password |

## Tool
`tools/get_hoopit_appointments.py`

## Steps
1. Ensure `.env` is populated with `HOOPIT_PHONE` and `HOOPIT_PASSWORD`.
2. Install dependencies (first time only):
   ```bash
   pip install -r requirements.txt
   ```
3. Run the tool:
   ```bash
   python tools/get_hoopit_appointments.py
   ```
4. The next 2 appointments print to terminal with title, group, date, time, and location.

## Auth Flow (how it works)
Hoopit is a Flutter web app backed by Django + Firebase. The auth sequence is:

1. `GET https://api.hoopit.io/auth` → extract CSRF token from HTML
2. `POST https://api.hoopit.io/auth/` with phone + password + CSRF → Django redirects to `app.hoopit.io/?token=<firebase_custom_token>`
3. Exchange custom token for Firebase ID token via Google Identity Toolkit (`accounts:signInWithCustomToken`)
4. Use the ID token as `Authorization: Bearer <id_token>` against `https://api.hoopit.io/app/users/current/events/`

## Expected Output
```
Next 2 upcoming appointment(s):

  1. G2014 fotballtrening fredag
     Group: Gutter 2014
     Date:  2026-03-27
     Time:  15:00–16:30
     Where: Ullernbanen

  2. Søndagstreninh Oldboys/Vet
     Group: Old/Boys og Veteran
     Date:  2026-03-29
     Time:  20:30–22:10
     Where: ullernbanen
```

## Edge Cases & Known Issues

### Login fails
- **Symptom:** "no token in redirect URL" error
- **Fix:** Double-check `HOOPIT_PHONE` and `HOOPIT_PASSWORD` in `.env`. Phone number should be digits only (no `+47` prefix).

### 401 Unauthorized on events endpoint
- **Cause:** Firebase token exchange failed, or the Firebase API key changed.
- **Fix:** Verify `FIREBASE_API_KEY` in the script matches what's in `app.hoopit.io/main.dart.js` (search for `AIzaSy`).

### CSRF token not found
- **Cause:** Hoopit updated their login page HTML.
- **Fix:** Inspect `https://api.hoopit.io/auth` in a browser, find the new `csrfmiddlewaretoken` input field name, update the regex in `get_firebase_token()`.

### No appointments returned
- The API returns events sorted by date. If the list is empty, there are genuinely no upcoming events.
