# Connecting your school's schedule

An adapter is a small Python module in `adapters/` that returns lessons and tests in the format of
[data-format.md](data-format.md). Choose one in `config.json` with `"adapter": "<module name>"`.

## Which one should I use?

```
Does the platform offer a calendar subscription / export link (iCal, .ics, webcal://)?
 ├─ yes ─▶ ical      (easiest, no password, keeps itself up to date)
 └─ no
     ├─ Is the timetable mostly the same every week? ─▶ manual  (type it once, add tests by hand)
     └─ Do the teachers write important notes in the platform, and does the child log in
        with a username + password (not BankID/SSO)? ─▶ a custom adapter (below)
```

The teacher notes are what make the "Ta med" list powerful. `ical` gets them when the platform puts
them in the event description; `manual` only has what you type; a custom adapter can usually get them.

## `ical`

1. Find the link in the platform: look for "Prenumerera", "Exportera", "Kalenderlänk", "iCal",
   "Lägg till i Google Kalender". On a phone app it may be under settings. A Google or Outlook
   calendar where you keep the schedule works as well ("Secret address in iCal format").
2. Put it in `.env` as `ICAL_URL=...` (it is a secret: anyone with the link can read the calendar).
3. `"adapter": "ical"` in `config.json`, then `python fetch.py --debug`.
4. Events whose title contains a word from `ical.test_keywords` become tests; everything else timed
   becomes a lesson. All-day events are ignored.

## `manual`

`cp timetable.example.json timetable.json` and fill in `week` (mon to fri), `tests` and `no_school`
(holidays). A `note` on a lesson like `"Ta med idrottskläder"` makes it show up in the packing list
every week. An AI assistant can turn a photo or copy of the printed timetable into this file.

## Writing your own adapter

Start from [`adapters/_template.py`](../adapters/_template.py). The process that worked for us:

1. **Look for an export or API first.** Many platforms have one for parents; it is more stable and
   clearly allowed. Read the platform's terms of use: automating your own login for private use is
   common but it is your call, and some platforms forbid it.
2. **Watch what the platform's own web page does.** Log in normally in a desktop browser, open
   DevTools (F12) > Network, filter on "Fetch/XHR", and open the calendar/schedule view. Look for a
   request whose response is JSON with lessons in it (fields like start, end, title, text). Note:
   - the URL and query parameters (date range, school/unit ids),
   - the method (GET/POST) and special headers (e.g. `X-Requested-With: XMLHttpRequest`),
   - how login works: usually a login page with a hidden token field, a POST, then redirects that set
     a session cookie. Python's `requests.Session()` handles cookies and redirects for you.
3. **Share structure, not data.** If an AI assistant helps you, give it the URL pattern (ids can be
   replaced) and a response sample where names, notes and ids are replaced by fake values.
   Never share passwords, cookies or `Authorization` headers.
4. **Some data may only be in the HTML.** Pages sometimes embed their data as JSON inside a
   `<script>`; a regular expression around that is often sturdier than parsing table cells.
5. **Map fields** to `title`, `start`, `end`, `location`, `text`, `kind: "lesson"` and for tests
   `id`, `title`, `type`, `date_text`, `subject`, `description`.
6. **Fail loudly and save evidence.** On unexpected responses raise an error with a clear message
   and, with `--debug`, save the raw page as `debug_*.html` (git-ignored, contains personal data:
   delete it when done). Because fetch.py stops before writing, the dashboard keeps the last good data.
7. **Be gentle.** Fetch every few hours, not every minute. Small `time.sleep()` between many requests.

Things that do *not* work for automation: BankID, Freja, SSO through the municipality with
two-factor authentication. Use `ical` or `manual` in those cases.

## Sharing an adapter

If you write an adapter for a platform others use, consider sharing it (a pull request is welcome):
no credentials, no ids specific to your school hard-coded (read them from `config.json`), and
example data with fake values only.
