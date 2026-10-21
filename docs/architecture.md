# Architecture

```
            every 3 h (systemd timer / cron / Task Scheduler)
                         │
                         ▼
 .env ──secrets──▶  fetch.py ──▶ adapters/<name>.py ──▶ school platform / calendar feed / timetable.json
 config.json ─────▶     │
                        ├── reminders  (lines in teacher notes matching remember_keywords)
                        ├── activities (weekly after-school activities from config.json)
                        ├── weather    (api.met.no, free, no key)
                        ├── study plans (rule-based, 25 min per day before each test)
                        ▼
                web/school_data.json
                        │  (read-only, fetched by the browser)
                        ▼
 server.py ──serves web/──▶ dashboard.html ⇄ clock.html (+ clock-core.js)
     │                                         │
     └── PUT /clock_config.json ◀──────────────┘  (clock settings from the ⚙️ dialog)
```

## Files

| Path | What | Committed? |
| --- | --- | --- |
| `fetch.py` | Orchestrates one data refresh | yes |
| `adapters/*.py` | One module per data source | yes (your own may contain URLs of your platform: fine, but no secrets) |
| `server.py` | Static file server for `web/` on port 8080 | yes |
| `web/dashboard.html` | Main screen: today, tomorrow, next week, sidebar | yes |
| `web/clock.html` | Full screen "get ready" clock and its settings | yes |
| `web/clock-core.js` | Shared clock logic (phases, school start, config load/save) | yes |
| `pi/` | Raspberry Pi installer, systemd units, kiosk, screen schedule, watchdog | yes |
| `config.json` | Your settings (adapter, location, activities, screen times) | **no** |
| `.env` | Secrets (calendar link, login) | **no** |
| `timetable.json` | Your typed timetable (manual adapter) | **no** |
| `web/school_data.json` | Generated data | **no** |
| `web/clock_config.json` | Saved clock settings | **no** |

## Behaviour worth knowing

- **Default tab follows the clock**: "Idag" before 12:00, "Imorgon" after. When nobody has touched
  the screen for 3 minutes it drifts back to the default tab.
- **Morning auto-switch**: when the clock's first phase starts (60 min before the first lesson by
  default), the dashboard opens `clock.html?auto=1`, which returns to the dashboard when the window
  is over. A touch on the screen postpones this by 5 minutes.
- **School start** for the clock is the first lesson of the day (`mode: auto`), a fixed time
  (`manual`) or nothing (`off`), per weekday.
- **Theme**: auto (dark 19:00 to 07:00), light or dark, toggled bottom right, stored in the browser.
- **Night**: with `?kiosk=1` in the URL the page turns fully black outside the `screen` hours.
  `pi/screen-power.sh` uses the same hours to dim a hardware backlight when there is one.
- **Lesson cards** open the full teacher note. Tests and words like "prov", "läxförhör",
  "redovisning" in notes get a purple chip so they stand out.
- The page reloads the data every 3 hours and re-renders every 30 seconds (countdowns, day change).

No build step, no framework, no database: everything is readable in a text editor.
