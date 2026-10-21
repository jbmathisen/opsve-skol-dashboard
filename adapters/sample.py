"""
Sample adapter: made-up lessons, notes and tests, always placed around the current date.

Use it to try the dashboard before connecting anything real. Every name, room and note here
is invented. It needs no settings and no secrets.
"""
from datetime import date, timedelta

# A fictional weekly timetable: weekday (0 = Monday) -> (start, end, subject, room)
TIMETABLE = {
    0: [("08:10", "09:00", "Matematik", "Sal 12"), ("09:15", "10:15", "Svenska", "Sal 7"),
        ("10:30", "11:30", "Engelska", "Sal 7"), ("12:30", "13:30", "NO", "Labbet"),
        ("13:45", "14:45", "Bild", "Ateljén")],
    1: [("08:30", "09:30", "Idrott och hälsa", "Idrottshallen"), ("09:50", "10:50", "SO", "Sal 3"),
        ("11:00", "11:50", "Matematik", "Sal 12"), ("13:00", "14:30", "Slöjd", "Slöjdsalen")],
    2: [("08:10", "09:10", "Engelska", "Sal 7"), ("09:20", "10:20", "Svenska", "Sal 7"),
        ("10:40", "11:40", "NO", "Labbet"), ("12:40", "13:40", "Musik", "Musiksalen")],
    3: [("08:10", "09:00", "Matematik", "Sal 12"), ("09:15", "10:45", "Hemkunskap", "Hemkunskapen"),
        ("11:00", "12:00", "SO", "Sal 3"), ("13:00", "14:00", "Idrott och hälsa", "Idrottshallen")],
    4: [("08:40", "09:40", "Svenska", "Sal 7"), ("09:50", "10:50", "Engelska", "Sal 7"),
        ("11:00", "11:50", "Matematik", "Sal 12"), ("12:50", "13:50", "Mentorstid", "Sal 3")],
}

# Teacher notes keyed by (subject, weekday). They exercise the "Ta med" and "Kom ihåg" lists.
NOTES = {
    ("Matematik", 0): "Vi börjar kapitel 4: bråk.\nTa med miniräknare och mattebok.",
    ("NO", 0): "Ta med dator (laddad), vi gör en digital labbrapport.",
    ("Idrott och hälsa", 1): "Vi är ute idag om vädret tillåter. Ta med utekläder och idrottskläder.",
    ("SO", 1): "Vi pratar om demokrati. Glöm inte att läsa sidorna 40 till 45 till torsdag.",
    ("Engelska", 2): "Glosor kapitel 3. Läxförhör på fredag!\nTa med hörlurar.",
    ("Hemkunskap", 3): "Vi bakar bullar. Kom ihåg förkläde och att sätta upp håret.",
    ("Svenska", 4): "Redovisning av bokrecensionerna, ta med din bok.",
    ("Mentorstid", 4): "Glöm inte att lämna in lappen om utflykten.",
}


def fetch(config: dict, start: date, end: date, debug: bool = False) -> dict:
    events = []
    d = start
    while d <= end:
        for (t0, t1, subject, room) in TIMETABLE.get(d.weekday(), []):
            events.append({
                "title": subject,
                "start": f"{d} {t0}",
                "end": f"{d} {t1}",
                "location": room,
                "text": NOTES.get((subject, d.weekday()), ""),
                "kind": "lesson",
            })
        d += timedelta(days=1)

    # Tests relative to this week's Monday so the countdowns always show something
    monday = start - timedelta(days=start.weekday())
    def day(offset_days: int, time: str) -> str:
        return f"{monday + timedelta(days=offset_days)} {time}"

    assignments = [
        {"id": "s1", "title": "Läxförhör glosor kapitel 3", "type": "Läxa", "date_text": day(4, "09:50"),
         "subject": "Engelska", "description": "Glosorna på sidan 32 i textboken."},
        {"id": "s2", "title": "Prov bråk och procent", "type": "Prov", "date_text": day(9, "08:10"),
         "subject": "Matematik", "description": "Kapitel 4, avsnitt 4.1 till 4.4."},
        {"id": "s3", "title": "Presentation: ett land i Europa", "type": "Presentation", "date_text": day(10, "11:00"),
         "subject": "SO", "description": "3 till 5 minuter, gärna med bilder."},
        {"id": "s4", "title": "Diagnos kemi", "type": "Diagnostiskt test", "date_text": day(25, "10:40"),
         "subject": "NO", "description": ""},
    ]
    return {"events": events, "assignments": assignments}
