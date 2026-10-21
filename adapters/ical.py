"""
iCal adapter: reads a calendar feed (.ics), the "subscribe to calendar" link many school
platforms, Google Calendar and Outlook offer. No password needed.

Setup:
  1. Find the export / subscribe link in your school platform (often "Prenumerera", "Exportera
     kalender", "iCal" or "webcal://..."). It usually contains a private token, so treat it
     like a password: put it in .env, never in config.json or a commit:
         ICAL_URL=https://.../calendar.ics
     (a local file path also works, handy for testing: ICAL_URL=./my-calendar.ics)
  2. "adapter": "ical" in config.json.

What becomes what:
  - Timed events            -> lessons (their DESCRIPTION becomes the teacher's note)
  - Titles matching any of config["ical"]["test_keywords"] (e.g. "prov") -> tests/assignments
  - All-day events          -> ignored (a holiday only removes lessons if the feed itself leaves them out)

Weekly and daily repeats (RRULE), EXDATE and moved single occurrences are handled.
Times with a TZID are treated as local wall-clock time (fine when the calendar and the
screen are in the same time zone); UTC times ("...Z") are converted to local time.
"""
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

DEFAULT_TEST_KEYWORDS = ["prov", "läxförhör", "förhör", "diagnos", "redovisning", "presentation", "inlämning"]
WEEKDAYS = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


def _load(source: str) -> str:
    if source.startswith("webcal://"):
        source = "https://" + source[len("webcal://"):]
    if source.startswith(("http://", "https://")):
        # The link contains a private token: never let it end up in error messages or logs,
        # which parents may paste into an AI chat or an issue.
        try:
            resp = requests.get(source, timeout=30, headers={"User-Agent": "school-dashboard"})
            resp.raise_for_status()
        except requests.RequestException as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            raise SystemExit(f"Kunde inte hämta kalendern ({type(e).__name__}"
                             f"{f', HTTP {status}' if status else ''}). Kontrollera ICAL_URL i .env "
                             "(länken visas inte här eftersom den är hemlig).") from None
        resp.encoding = resp.encoding or "utf-8"
        return resp.text
    return Path(source).read_text(encoding="utf-8")


def _unfold(text: str) -> list[str]:
    """RFC 5545: lines starting with a space or tab continue the previous line."""
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        elif raw:
            lines.append(raw)
    return lines


def _unescape(v: str) -> str:
    return v.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def _parse_dt(value: str, params: str) -> tuple[datetime, bool]:
    """Returns (naive local datetime, all_day)."""
    if "VALUE=DATE" in params.upper() or re.fullmatch(r"\d{8}", value):
        return datetime.strptime(value[:8], "%Y%m%d"), True
    dt = datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    if value.endswith("Z"):
        dt = dt.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)
    return dt, False


def _events(text: str) -> list[dict]:
    out, cur = [], None
    for line in _unfold(text):
        if line == "BEGIN:VEVENT":
            cur = {"exdates": set()}
        elif line == "END:VEVENT" and cur is not None:
            out.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            head, value = line.split(":", 1)
            name, _, params = head.partition(";")
            name = name.upper()
            if name in ("DTSTART", "DTEND", "RECURRENCE-ID"):
                cur[name], all_day = _parse_dt(value, params)
                if name == "DTSTART":
                    cur["all_day"] = all_day
            elif name == "EXDATE":
                for v in value.split(","):
                    cur["exdates"].add(_parse_dt(v, params)[0])
            elif name == "RRULE":
                cur["RRULE"] = dict(p.split("=", 1) for p in value.split(";") if "=" in p)
            elif name in ("SUMMARY", "LOCATION", "DESCRIPTION", "UID"):
                cur[name] = _unescape(value)
    return out


def _occurrences(ev: dict, start: date, end: date):
    """Yields start datetimes of an event (expanding WEEKLY/DAILY repeats) within [start, end]."""
    first = ev["DTSTART"]
    rule = ev.get("RRULE")
    if not rule:
        if start <= first.date() <= end:
            yield first
        return
    freq = rule.get("FREQ")
    interval = int(rule.get("INTERVAL", 1))
    count = int(rule["COUNT"]) if "COUNT" in rule else None
    until = _parse_dt(rule["UNTIL"], "")[0] if "UNTIL" in rule else None
    if freq == "WEEKLY":
        days = sorted(WEEKDAYS[d[-2:]] for d in rule.get("BYDAY", "").split(",") if d) or [first.weekday()]
        week0 = first - timedelta(days=first.weekday())
        step = timedelta(weeks=interval)
        offsets = [timedelta(days=d) for d in days]
    elif freq == "DAILY":
        week0, step, offsets = first, timedelta(days=interval), [timedelta(0)]
    else:
        return  # MONTHLY/YEARLY are rare for school schedules
    n, base = 0, week0
    while base.date() <= end:
        for off in offsets:
            occ = base + off
            if occ < first:
                continue
            if (until and occ > until) or (count is not None and n >= count):
                return
            n += 1
            if start <= occ.date() <= end and occ not in ev["exdates"]:
                yield occ
        base += step


def fetch(config: dict, start: date, end: date, debug: bool = False) -> dict:
    source = os.environ.get("ICAL_URL", "").strip()
    if not source:
        raise SystemExit("ICAL_URL saknas. Lägg kalenderlänken i .env (se .env.example).")
    keywords = [k.lower() for k in config.get("ical", {}).get("test_keywords", DEFAULT_TEST_KEYWORDS)]

    raw = _events(_load(source))
    # Single occurrences that were moved/changed replace the generated ones
    overridden = {(e.get("UID"), e["RECURRENCE-ID"]) for e in raw if "RECURRENCE-ID" in e}

    events, assignments = [], []
    for ev in raw:
        if "DTSTART" not in ev or ev.get("all_day"):
            continue
        length = (ev["DTEND"] - ev["DTSTART"]) if "DTEND" in ev else timedelta(hours=1)
        title = (ev.get("SUMMARY") or "").strip()
        is_test = any(k in title.lower() for k in keywords)
        for occ in _occurrences(ev, start, end):
            if "RECURRENCE-ID" not in ev and (ev.get("UID"), occ) in overridden:
                continue
            s, e = occ.strftime("%Y-%m-%d %H:%M"), (occ + length).strftime("%Y-%m-%d %H:%M")
            if is_test:
                assignments.append({
                    "id": f"{ev.get('UID', title)}@{s}",
                    "title": title,
                    "type": next((k.capitalize() for k in keywords if k in title.lower()), "Prov"),
                    "date_text": s,
                    "subject": "",  # filled in below from the lesson at the same time
                    "description": (ev.get("DESCRIPTION") or "").strip(),
                })
            else:
                events.append({
                    "title": title,
                    "start": s,
                    "end": e,
                    "location": (ev.get("LOCATION") or "").strip(),
                    "text": (ev.get("DESCRIPTION") or "").strip(),
                    "kind": "lesson",
                })
    for a in assignments:
        a["subject"] = next((e["title"] for e in events if e["start"] <= a["date_text"] < e["end"]), "")
    if debug:
        print(f"[DEBUG] ical: {len(raw)} VEVENTs -> {len(events)} lektioner, {len(assignments)} prov", file=sys.stderr)
    return {"events": sorted(events, key=lambda x: x["start"]), "assignments": assignments}
