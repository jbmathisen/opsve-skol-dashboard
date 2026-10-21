"""
Template for your own adapter, e.g. for a school platform that has no calendar export.

    cp adapters/_template.py adapters/myschool.py      then  "adapter": "myschool" in config.json

Read docs/adapters.md first. In short:
  1. Prefer an official API or export over scraping. Check the platform's terms of use.
  2. Find the requests the platform's own web page makes (browser DevTools > Network).
     Look for responses that already are JSON with the lessons in them.
  3. Use your own (or your child's) login only, on your own machine. Put it in .env.
     Never paste passwords, cookies or tokens into a chat with an AI or into an issue.
  4. When you show an AI what a response looks like, share the *structure* with
     names, notes and IDs replaced by fake values.
  5. Fail loudly: if login stops working, raise an error with a clear message so the
     dashboard keeps showing the last good data instead of an empty week.

The skeleton below shows the common pattern for a classic username/password form login
with a hidden anti-forgery (CSRF) token. Everything in CAPITALS is a placeholder.
"""
import os
import sys
from datetime import date
from pathlib import Path

import requests

BASE_URL = "https://SCHOOL-PLATFORM.EXAMPLE"   # placeholder: your platform's address


def login(session: requests.Session, debug: bool) -> None:
    username = os.environ["SCHOOL_USERNAME"]   # from .env, never hard-coded
    password = os.environ["SCHOOL_PASSWORD"]

    # 1. Load the login page and pick up the hidden token the form posts back
    page = session.get(f"{BASE_URL}/LOGIN-PAGE")
    page.raise_for_status()
    from bs4 import BeautifulSoup  # pip install beautifulsoup4
    token_input = BeautifulSoup(page.text, "html.parser").find("input", {"name": "HIDDEN-TOKEN-FIELD"})
    if not token_input:
        Path("debug_login_page.html").write_text(page.text, encoding="utf-8")  # git-ignored
        raise RuntimeError("Hittade inte inloggningsformulärets token. Har sidan ändrats? Se debug_login_page.html")

    # 2. Post the form; requests follows the redirects and keeps the session cookie
    resp = session.post(f"{BASE_URL}/LOGIN-POST-URL", data={
        "USERNAME-FIELD": username,
        "PASSWORD-FIELD": password,
        "HIDDEN-TOKEN-FIELD": token_input["value"],
    })
    resp.raise_for_status()

    # 3. Verify it worked (e.g. you ended up on the app's start page, not back on the login page)
    if "LOGIN-PAGE" in resp.url:
        raise RuntimeError("Inloggningen misslyckades. Kontrollera användarnamn och lösenord i .env.")
    if debug:
        print(f"[DEBUG] inloggad, hamnade på {resp.url}", file=sys.stderr)


def fetch(config: dict, start: date, end: date, debug: bool = False) -> dict:
    session = requests.Session()
    session.headers["User-Agent"] = "school-dashboard (private family use)"
    login(session, debug)

    # Ask for the schedule the same way the platform's own calendar page does
    resp = session.get(f"{BASE_URL}/CALENDAR-ENDPOINT", params={"start": start.isoformat(), "end": end.isoformat()})
    resp.raise_for_status()

    events = []
    for item in resp.json():  # map the platform's fields to the dashboard's format
        events.append({
            "title": item["SUBJECT-FIELD"],
            "start": item["START-FIELD"],      # must become "YYYY-MM-DD HH:MM"
            "end": item["END-FIELD"],
            "location": item.get("ROOM-FIELD", ""),
            "text": item.get("NOTE-FIELD", ""),
            "kind": "lesson",
        })

    assignments = []  # same idea for tests/homework, if the platform has them
    return {"events": events, "assignments": assignments}
