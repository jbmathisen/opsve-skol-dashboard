# Without a Raspberry Pi

The dashboard is a static web page plus a small Python script, so any always-on device at home
can run it. What you need: something that runs `fetch.py` every few hours and `server.py` all the time,
and a screen that shows `http://<that-device>:8080/dashboard.html`.

## A Windows, Mac or Linux computer

1. Install Python 3.10+ and run `pip install -r requirements.txt` in the folder.
2. `cp config.example.json config.json` and adjust; secrets in `.env`.
3. Run `python server.py` at login, and `python fetch.py` on a schedule:
   - **Windows**: Task Scheduler. One task "At log on": `python server.py` (start in the repo folder).
     One task daily, repeat every 3 hours: `python fetch.py`.
   - **Mac**: a `launchd` agent, or simply `crontab -e`:
     `0 */3 * * * cd /path/to/repo && /usr/bin/python3 fetch.py`
   - **Linux**: reuse the systemd units in `pi/` (replace `__APP_DIR__` and `__APP_USER__`).
4. Open `http://localhost:8080/dashboard.html`. Other devices at home use the computer's IP address
   (allow port 8080 in the firewall for the *private* network only).

## A NAS or home server (Synology, Unraid, an old laptop)

Same as above: Python plus two scheduled jobs. With Docker, a plain `python:3.12-slim` container
that mounts the folder and runs `python server.py`, plus a scheduled `python fetch.py`, is enough.

## The screen: an old tablet or phone

Open the dashboard URL in the browser, add it to the home screen, and use the device's kiosk or
"guided access" mode (iPad: Guided Access; Android: screen pinning or a kiosk browser app).
Add `?kiosk=1` to the URL if it should go black at night. Keep it on a charger.

## Viewing it away from home

Do **not** open a port in your router or upload real data to a public site: the page has no login
and shows your child's whereabouts during the day. If you want access from your phone outside the
home, use a private VPN such as Tailscale or WireGuard.

A public demo is fine with the `sample` adapter only: build it with `python fetch.py` and host the
`web/` folder anywhere static (e.g. GitHub Pages). Saving clock settings then only works per browser.
