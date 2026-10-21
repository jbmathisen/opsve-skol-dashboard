"""
Adapters turn *your* school's schedule into the dashboard's format.

Every adapter is a module in this folder with one function:

    def fetch(config: dict, start: date, end: date, debug: bool = False) -> dict:
        return {"events": [...], "assignments": [...]}

- config      the parsed config.json (adapter settings live under config[<adapter name>])
- start, end  the date range to fetch (this Monday until three weeks ahead)
- secrets     read them from os.environ (fetch.py loads .env); never from config.json

Event (a lesson):
    {"title": "Matematik", "start": "2026-09-07 08:10", "end": "2026-09-07 09:00",
     "location": "Sal 12", "text": "Teacher's note, may be empty", "kind": "lesson"}

Assignment (test, homework, presentation...):
    {"id": "any-unique-id", "title": "Prov kapitel 3", "type": "Prov",
     "date_text": "2026-09-15 10:00", "subject": "Matematik", "description": ""}

Included: sample (made-up demo data), manual (a weekly timetable you type in), ical (a calendar feed).
Copy _template.py to write your own. Full guide: docs/adapters.md
"""
