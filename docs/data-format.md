# Data format: `web/school_data.json`

This is the contract between the back end and the dashboard. An adapter only has to produce
`events` and `assignments`; `fetch.py` adds the rest.

```json
{
  "fetched_at": "2026-09-07T06:00",
  "source": "ical",
  "week_start": "2026-09-07",
  "fetch_end": "2026-09-28",

  "events": [
    {
      "title": "Engelska",
      "start": "2026-09-07 09:10",
      "end": "2026-09-07 10:10",
      "location": "Sal 7",
      "text": "We read chapter 3.\nTa med hörlurar.",
      "kind": "lesson"
    }
  ],

  "assignments": [
    {
      "id": "a1",
      "title": "Prov kapitel 4",
      "type": "Prov",
      "date_text": "2026-09-15 08:10",
      "subject": "Matematik",
      "description": "Avsnitt 4.1 till 4.4"
    }
  ],

  "reminders": [
    { "date": "2026-09-07", "subject": "Engelska", "note": "Ta med hörlurar." }
  ],

  "extra_activities": [
    { "title": "Fotboll", "date": "2026-09-08", "start": "2026-09-08 17:00", "end": "2026-09-08 18:30", "is_extra": true }
  ],

  "study_plans": [
    {
      "title": "Prov kapitel 4", "subject": "Matematik", "type": "Prov",
      "test_date": "2026-09-15", "days_until": 8,
      "daily_tasks": [ { "date": "2026-09-07", "task": "Läs igenom materialet", "minutes": 25 } ]
    }
  ],

  "weather": {
    "today":    { "date": "2026-09-07", "temp_min": 9, "temp_max": 16, "symbol": "partlycloudy_day", "precip_max": 0.4, "wind_max": 5 },
    "tomorrow": { "date": "2026-09-08", "temp_min": 8, "temp_max": 14, "symbol": "rain", "precip_max": 2.1, "wind_max": 7 }
  },

  "screen": { "weekday_on": "06:30", "weekend_on": "10:00", "off": "21:30" }
}
```

## Rules for adapters

- Times are local wall-clock time as `"YYYY-MM-DD HH:MM"` (a space, not a `T`).
- `kind` must be `"lesson"` for anything that should appear on the timeline and count as school start.
  Other values (e.g. `"event"`) are kept in the file but not shown.
- `text` is the teacher's free-text note. It drives the "Ta med" and "Kom ihåg" lists, so keep line
  breaks (`\n`). HTML is tolerated (it is stripped), plain text is better.
- `title` should be the subject name. Tests are matched to a lesson by time or by subject name.
- `assignments[].type` is shown as a label. Titles containing "prov", "läxförhör", "förhör" or
  "diagnos" are treated as important (strong purple chip); "redovisning", "presentation",
  "inlämning" as softer ones.
- `id` must be unique per assignment (any string).
- Optional: `"allDay": true` on events that should be ignored.
- `weather.symbol` uses MET Norway symbol codes; unknown codes show a thermometer.
