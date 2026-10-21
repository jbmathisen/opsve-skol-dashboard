"""
Manual adapter: you type the weekly timetable and upcoming tests into timetable.json.

Works with any school, needs no login at all. Good when the platform has no export
or you do not want to give a script your child's credentials.

    cp timetable.example.json timetable.json   (then edit it)
    "adapter": "manual" in config.json

timetable.json is git-ignored because it describes your child's real week.
Teacher notes cannot come from here (unless you type them in "notes"), so the
"Ta med" list is built from the "notes" you add per lesson and weekday.
"""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


def fetch(config: dict, start: date, end: date, debug: bool = False) -> dict:
    name = config.get("manual", {}).get("file", "timetable.json")
    path = ROOT / name
    if not path.exists():
        raise SystemExit(f"Hittade inte {path}. Kopiera timetable.example.json till {name} och fyll i schemat.")
    tt = json.loads(path.read_text(encoding="utf-8"))

    skip = set(tt.get("no_school", []))  # holidays, "YYYY-MM-DD"
    events = []
    d = start
    while d <= end:
        if d.isoformat() not in skip:
            for day_key, lessons in tt.get("week", {}).items():
                if DAYS[day_key] != d.weekday():
                    continue
                for l in lessons:
                    events.append({
                        "title": l["subject"],
                        "start": f"{d} {l['start']}",
                        "end": f"{d} {l['end']}",
                        "location": l.get("room", ""),
                        "text": l.get("note", ""),
                        "kind": "lesson",
                    })
        d += timedelta(days=1)

    assignments = []
    for i, a in enumerate(tt.get("tests", [])):
        assignments.append({
            "id": f"m{i}",
            "title": a["title"],
            "type": a.get("type", "Prov"),
            "date_text": f"{a['date']} {a.get('time', '')}".strip(),
            "subject": a.get("subject", ""),
            "description": a.get("description", ""),
        })
    return {"events": events, "assignments": assignments}
