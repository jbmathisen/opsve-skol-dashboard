#!/usr/bin/env python3
"""
fetch.py: builds web/school_data.json, the only file the dashboard reads.

    python fetch.py            # uses config.json (or config.example.json if you have none yet)
    python fetch.py --debug    # more logging, adapters may save raw responses as debug_*.html

Steps:
  1. Runs the adapter named in config.json ("adapter": "sample" | "manual" | "ical" | your own)
     to get lessons (events) and tests/homework (assignments). See adapters/ and docs/adapters.md.
  2. Extracts "remember / bring" lines from the teachers' notes (keywords in config.json).
  3. Adds after-school activities, weather (MET Norway / Yr, free) and simple study plans.
  4. Writes everything to web/school_data.json (format: docs/data-format.md).

Run it on a timer (the Pi installer sets up a systemd timer every 3 hours).
Secrets (passwords, private calendar links) go in .env, never in config.json or the code.
"""

import importlib
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # python-dotenv is optional: you can also set the variables in the environment

ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = ROOT / "web" / "school_data.json"
DEBUG = "--debug" in sys.argv


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def load_config() -> dict:
    path = ROOT / "config.json"
    if not path.exists():
        log("[!] config.json saknas, använder config.example.json (kopiera den och anpassa).")
        path = ROOT / "config.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


def build_remember_list(events: list[dict], keywords: list[str]) -> list[dict]:
    """Picks lines out of the teachers' notes that match the keywords (e.g. "ta med", "glöm inte")."""
    keywords = [k.lower() for k in keywords]
    reminders = []
    for ev in events:
        text = (ev.get("text") or "").replace("\r\n", "\n")
        for line in text.split("\n"):
            line_clean = line.strip("-• \t")
            if line_clean and any(kw in line_clean.lower() for kw in keywords):
                reminders.append({
                    "date": ev["start"].split(" ")[0],
                    "subject": ev.get("title", ""),
                    "note": line_clean,
                })
    return reminders


def build_extra_activities(activities: list[dict], start: date, end: date) -> list[dict]:
    """Expands weekly after-school activities from config.json into dated entries."""
    out = []
    current = start
    while current <= end:
        for act in activities:
            if current.weekday() == act["weekday"]:
                d = current.isoformat()
                out.append({
                    "title": act["title"],
                    "date": d,
                    "start": f"{d} {act['start']}",
                    "end": f"{d} {act['end']}",
                    "is_extra": True,
                })
        current += timedelta(days=1)
    return out


def fetch_weather(cfg: dict) -> dict | None:
    """Today's and tomorrow's forecast from MET Norway (api.met.no), free and without API key."""
    if not cfg.get("enabled", True):
        return None
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={cfg['lat']}&lon={cfg['lon']}"
    try:
        # MET asks for an identifying User-Agent (their terms of service)
        resp = requests.get(url, timeout=10, headers={"User-Agent": cfg.get("user_agent", "school-dashboard")})
        resp.raise_for_status()
        series = resp.json().get("properties", {}).get("timeseries", [])
    except Exception as e:
        log(f"[WARN] Kunde inte hämta väder: {e}")
        return None

    points = []
    for ts in series:
        dt = datetime.fromisoformat(ts["time"].replace("Z", "+00:00")).astimezone()  # local time
        data = ts.get("data", {})
        nxt = data.get("next_1_hours", {}) or data.get("next_6_hours", {})
        points.append({
            "date": dt.strftime("%Y-%m-%d"),
            "hour": dt.hour,
            "temp": data.get("instant", {}).get("details", {}).get("air_temperature"),
            "wind": data.get("instant", {}).get("details", {}).get("wind_speed"),
            "symbol": nxt.get("summary", {}).get("symbol_code", ""),
            "precip": nxt.get("details", {}).get("precipitation_amount", 0),
        })

    def day_summary(day: str) -> dict | None:
        pts = [p for p in points if p["date"] == day]
        temps = [p["temp"] for p in pts if p["temp"] is not None]
        if not temps:
            return None
        midday = [p for p in pts if 10 <= p["hour"] <= 14]
        return {
            "date": day,
            "temp_min": round(min(temps)),
            "temp_max": round(max(temps)),
            "symbol": (midday or pts)[0]["symbol"],
            "precip_max": round(max(p["precip"] or 0 for p in pts), 1),
            "wind_max": round(max(p["wind"] or 0 for p in pts)),
        }

    today = date.today()
    return {"today": day_summary(today.isoformat()), "tomorrow": day_summary((today + timedelta(days=1)).isoformat())}


STUDY_PHASES = [
    ("Läs igenom materialet", 0.30),
    ("Sammanfatta och skriv ner nyckelbegrepp", 0.25),
    ("Öva med frågor eller uppgifter", 0.25),
    ("Testa dig själv / repetera", 0.20),
]


def build_study_plans(assignments: list[dict], today: date, days_ahead: int = 21) -> list[dict]:
    """Rule-based daily 25-minute study sessions leading up to each test (read, summarise, practise, repeat)."""
    plans = []
    for a in assignments:
        try:
            test_date = date.fromisoformat((a.get("date_text") or "").split(" ")[0])
        except ValueError:
            continue
        days_until = (test_date - today).days
        if days_until < 1 or days_until > days_ahead:
            continue
        study_days = max(1, days_until - 1)
        tasks = []
        for offset in range(study_days):
            progress, cumulative, label = offset / study_days, 0.0, STUDY_PHASES[-1][0]
            for phase_label, fraction in STUDY_PHASES:
                cumulative += fraction
                if progress < cumulative:
                    label = phase_label
                    break
            tasks.append({"date": (today + timedelta(days=offset)).isoformat(), "task": label, "minutes": 25})
        plans.append({
            "title": a["title"],
            "subject": a.get("subject", ""),
            "type": a.get("type", ""),
            "test_date": test_date.isoformat(),
            "days_until": days_until,
            "daily_tasks": tasks,
        })
    return sorted(plans, key=lambda p: p["test_date"])


def main() -> None:
    config = load_config()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    fetch_end = today + timedelta(days=21)  # three weeks ahead: covers "next week" and study plans

    name = config.get("adapter", "sample")
    log(f"Hämtar schema med adaptern '{name}'...")
    adapter = importlib.import_module(f"adapters.{name}")
    result = adapter.fetch(config, week_start, fetch_end, debug=DEBUG)
    events, assignments = result.get("events", []), result.get("assignments", [])

    data = {
        "fetched_at": datetime.now().isoformat(timespec="minutes"),
        "source": name,
        "week_start": week_start.isoformat(),
        "fetch_end": fetch_end.isoformat(),
        "events": events,
        "assignments": assignments,
        "reminders": build_remember_list(events, config.get("remember_keywords", [])),
        "weather": fetch_weather(config.get("weather", {"enabled": False})),
        "extra_activities": build_extra_activities(config.get("activities", []), week_start, fetch_end),
        "study_plans": build_study_plans(assignments, today),
        "screen": config.get("screen", {}),
    }

    OUTPUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Klart: {len(events)} lektioner, {len(assignments)} prov/uppgifter, "
        f"{len(data['reminders'])} påminnelser, väder: {'ja' if data['weather'] else 'nej'} -> {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
