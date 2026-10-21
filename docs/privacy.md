# Privacy and security

A school schedule tells anyone reading it where a child is during the day, and school credentials
often open more than the schedule. Treat both carefully.

## Where things live

| Data | File | In git? |
| --- | --- | --- |
| Passwords, private calendar links | `.env` | never |
| Your adapter choice, home coordinates, activities | `config.json` | never |
| Typed timetable | `timetable.json` | never |
| The fetched schedule and teacher notes | `web/school_data.json` | never |
| Clock settings | `web/clock_config.json` | never |
| Raw pages saved while debugging | `debug_*` | never (delete them when done) |

All of these are in `.gitignore`. Before every push, run `git status` and look.

## Rules of thumb

- **Credentials stay on the device that needs them.** Type them into `.env` yourself. On the Pi the
  installer makes `.env` readable only by its owner.
- **Never paste secrets into an AI chat**, an issue, a screenshot or a forum post. If you did, change
  the password or regenerate the calendar link.
- **Use the least powerful access that works.** A read-only calendar link beats a login. A typed
  timetable beats both if the platform only offers a login you are not comfortable automating.
- **Home network only.** `server.py` has no authentication. No port forwarding, no public hosting of
  real data. Use a VPN (Tailscale, WireGuard) for remote access.
- **Respect the platform.** Check its terms of use; fetch every few hours, not constantly.
- **Weather is the only outside call** besides your school platform: it sends your coordinates to
  MET Norway. Round them to 2 decimals (about 1 km) or disable weather.
- **Sharing screenshots or a demo?** Use the `sample` adapter. Real data contains teacher names,
  rooms and notes.
- **AI assistants see what they read.** Anything an AI coding tool opens is sent to its provider.
  The repo blocks `.env` for Claude Code (`.claude/settings.json`), Cursor (`.cursorignore`) and Aider
  (`.aiderignore`); with other tools, check their ignore settings before you create `.env`.
  Ask the assistant to work with counts and structure rather than reading your child's full schedule.
- **Logs can contain secrets.** The included adapters never print passwords or calendar links. Before
  you paste an error anywhere, look it over for anything that looks like a token or a name.
- **Guest Wi-Fi.** Anyone on the same network can open the dashboard and change the clock settings.
  Keep the Pi on your private network, not the guest network, and don't give guests the main one if
  you can avoid it.
- **Talk with your child** about what the screen shows and where it hangs. It is their schedule.

## Found a security problem in this repo?

Open an issue without including any personal data or credentials.
