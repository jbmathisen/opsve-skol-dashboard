# AGENTS.md: guide for AI assistants helping a parent set this up

You are helping a parent (often not a developer) build a school dashboard for their child.
Read this file fully, then [README.md](README.md) and [docs/architecture.md](docs/architecture.md).
Work in small steps, explain in plain language, and confirm each step works before the next.
Speak the parent's language (the interface is Swedish; many users will be Swedish speaking).

## Non-negotiable safety rules

1. **Never ask for, accept or repeat passwords, tokens, cookies or private calendar links in chat.**
   The parent types them into `.env` themselves. If they paste one anyway, tell them to change it
   (the password, or regenerate the link) and do not write it into any file yourself.
2. **Never commit or publish personal files**: `.env`, `config.json`, `timetable.json`, `*.ics`,
   `web/school_data.json`, `web/clock_config.json`, `debug_*`. They are in `.gitignore`; keep it that way.
   Before any `git push`, run `git status` and check that none of them is staged.
3. **No real personal data in code or docs.** No child's name, school name, teacher names or
   initials, home location or IP addresses in committed files. Use placeholders.
4. **Do not expose the dashboard to the internet** (no port forwarding, no public hosting of real
   data). It has no login. For access away from home, suggest a VPN such as Tailscale or WireGuard.
5. **Scraping a school platform is the parent's decision and responsibility.** Prefer, in order:
   an official export/API or calendar feed, then typing the timetable manually, then a custom
   adapter using the parent's own login. Mention that they should check the platform's terms.
6. When looking at raw responses from a school platform, ask the parent to **redact names, notes
   and IDs** first, or to share only the field names and structure.
7. **Do not read `.env` yourself**, not even "to check it". Whatever you read is sent to your model
   provider. To verify that values are set without revealing them, run:
   `python -c "import os,dotenv; dotenv.load_dotenv(); print({k: bool(os.getenv(k)) for k in ['ICAL_URL','SCHOOL_USERNAME','SCHOOL_PASSWORD']})"`.
   This repo ships `.claude/settings.json`, `.cursorignore` and `.aiderignore` that block it; never weaken them.
8. **Be sparing with the child's real data.** Everything you read (`web/school_data.json`, `debug_*`
   files, `timetable.json`, fetch logs) leaves the computer. Prefer counts and structure
   (`python fetch.py` prints a summary) over dumping whole files, and tell the parent when you need to
   look at real content.
9. **Never print, log or put secrets into error messages** in code you write (adapters included):
   no passwords, cookies, tokens or full URLs that contain tokens. Logs get pasted into chats.

## The setup process

Track progress with the parent through these phases. Skip what does not apply.

### Phase 0: get to know the situation (ask, do not assume)

- Who is it for (age, what is hard: mornings, remembering things, tests, changes in the schedule)?
- Where will it be shown: a Raspberry Pi with a screen, an old tablet, a computer that is always on?
- Which school platform does the school use, and does it offer a calendar export / subscribe link,
  an app with an export, or only a web login? Does the child log in with a password or with
  BankID/SSO? (BankID/SSO usually rules out an automated login: go for iCal or manual.)
- Their comfort with the terminal. Adjust explanations accordingly.

### Phase 1: demo with sample data (always do this first)

```bash
pip install -r requirements.txt
python fetch.py            # adapter "sample" by default
python server.py           # open http://localhost:8080/dashboard.html
```

Let the parent click around: tabs, a lesson card (opens the full teacher note), the clock in the
header (opens `clock.html`), `clock.html?time=07:25` to preview the morning colours.
Ask what they like and what does not fit their child. Note it for phase 3.

### Phase 2: connect the real schedule

Create the personal config: `cp config.example.json config.json`, then pick an adapter
(details in [docs/adapters.md](docs/adapters.md)):

- **ical**: parent finds the subscribe link, puts `ICAL_URL=...` in `.env`, set `"adapter": "ical"`.
  Run `python fetch.py --debug` and look at the counts. Check that lessons and tests were classified
  sensibly; tune `ical.test_keywords` in `config.json`.
- **manual**: `cp timetable.example.json timetable.json`, help the parent fill in the week (they can
  read it out or paste the timetable; mention that this shares it with the AI provider, so leave out
  names and the school's name, subjects and times are enough),
  set `"adapter": "manual"`.
- **custom adapter**: copy `adapters/_template.py`. Guide the parent to open the platform in their
  browser, DevTools > Network, find the request that returns the calendar (often JSON), and share
  the URL pattern and a redacted sample. Write the adapter to output exactly the format in
  [docs/data-format.md](docs/data-format.md). Credentials come from `os.environ` only.
  Add clear error messages for "login failed" and "page structure changed".

Done when `python fetch.py` reports the expected number of lessons and the dashboard shows the
real week correctly (check today, tomorrow and next week).

### Phase 3: personalize (in `config.json` and the web files)

See [docs/customizing.md](docs/customizing.md). Typical requests:
- weather location (`weather.lat`/`lon`, rounded to 2 decimals is plenty),
- after-school activities (`activities`, weekday 0 = Monday),
- packing keywords (`remember_keywords` and `PACK_DEFS` in `web/dashboard.html`),
- the morning clock: phases, tasks and school start per day (the settings button in `clock.html`),
- language of the interface, colours, the child's name in the greeting (stays local if you only
  change their copy; do not commit it to a public fork).

Keep the [design principles](docs/design-principles.md) in mind: fewer things, larger text, the
same colour always means the same thing, concrete tasks.

### Phase 4: deploy

- Raspberry Pi wall screen: [docs/raspberry-pi.md](docs/raspberry-pi.md)
- Existing computer / NAS / tablet: [docs/web-setup.md](docs/web-setup.md)

Done when the screen shows the dashboard after a reboot without anyone touching it, and data
refreshes on its own (check "Uppdaterad: ..." at the bottom right).

### Phase 5: hand-over

Tell the parent how to: fetch now, see logs, update files, and what to do when the platform
changes (run `python fetch.py --debug`, look at the error, adjust the adapter). Suggest they
revisit the setup with the child after a week: what helped, what was noise.

## Repo map and invariants

- `fetch.py`: runs the adapter, adds reminders, weather, activities, study plans, writes `web/school_data.json`.
- `adapters/`: one module per data source, each exposing `fetch(config, start, end, debug) -> {"events", "assignments"}`.
- `server.py`: static server for `web/`, plus `PUT /clock_config.json` so clock settings survive the kiosk's incognito browser.
- `web/dashboard.html`, `web/clock.html`, `web/clock-core.js`: plain HTML/JS, no build step, no framework.
- `pi/`: systemd units, kiosk autostart, screen schedule, watchdog, installer.

Invariants: the web page only reads local JSON and never contacts the school platform; secrets only
in `.env`; adapters output the documented format so the frontend never needs platform-specific code.
Text shown to the child avoids long dashes and keeps sentences short.
