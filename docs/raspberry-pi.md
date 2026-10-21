# Raspberry Pi wall screen

## Hardware

- Any Raspberry Pi 3B or newer (a 3B is enough), power supply, microSD card (16 GB+).
- A screen. HDMI screens from 7 to 10 inches work well; a touch screen lets the child tick off
  tasks on the clock and open lesson notes. The original was a 10.1" 1280x800 HDMI touch screen.
- Something to mount it near where the child gets ready (hallway, kitchen).

## 1. Prepare the SD card

Use **Raspberry Pi Imager**: choose "Raspberry Pi OS (64-bit)" *with desktop*. In the settings
(gear icon / "Edit settings") set a hostname, a username and password, your Wi-Fi, and enable SSH.
These values stay on the card: do not share them.

Boot the Pi with the screen attached. Find its IP address in your router's device list (or try
`ssh <user>@<hostname>.local`).

## 2. Put the code on the Pi

From the Pi (SSH or a keyboard):

```bash
git clone https://github.com/jbmathisen/opsve-skol-dashboard.git ~/school-dashboard
cd ~/school-dashboard
```

If you made your own changes on your computer (your adapter, translations), either push them to
**your own private fork** and clone that, or copy the files over with `scp` (see "Updating" below).

Then add your personal files on the Pi (they are not in git):

```bash
cp config.example.json config.json && nano config.json      # adapter, location, activities, screen hours
nano .env                                                    # only if your adapter needs a secret
```

## 3. Install

```bash
sudo bash pi/install.sh
sudo raspi-config        # System Options > Boot / Auto Login > Desktop Autologin
sudo reboot
```

The installer: installs packages, creates `config.json` if missing, installs the web server and a
fetch timer (every 3 hours) as systemd services, adds the screen schedule and a watchdog to cron,
and starts Chromium in kiosk mode at login.

Useful commands:

```bash
systemctl status school-dashboard school-fetch.timer
sudo systemctl start school-fetch && journalctl -u school-fetch -n 30     # fetch now, show log
sudo systemctl restart lightdm      # reload the kiosk browser (e.g. after changing web files)
```

## Screen settings (only if the picture is wrong)

Most HDMI screens just work. If yours shows the wrong resolution, add lines to
`/boot/firmware/config.txt` (make a backup first). Example for a 1280x800 HDMI screen:

```
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt 1280 800 60 6 0 0
hdmi_drive=1
config_hdmi_boost=7
```

On recent Raspberry Pi OS versions with the KMS driver you may instead need
`video=HDMI-A-1:1280x800@60D` at the end of the single line in `/boot/firmware/cmdline.txt`.
Check your screen vendor's wiki.

## Lessons learned (save yourself an evening)

- **Never switch HDMI off at night.** Turning the output off with `wlr-randr --off` made the screen
  sometimes fail to wake up (black until reboot). Instead the page paints itself black at night and
  `screen-power.sh` only dims a backlight if one exists.
- **The Pi has no battery clock.** After a power cut the time is wrong until it syncs over the
  network, so the screen schedule waits for NTP before acting.
- **Stuck at the login screen** after some boots: the watchdog restarts the display manager if
  the kiosk browser is not running after 5 minutes. Make sure Desktop Autologin is on.
- **Emoji icons need a font**: `fonts-noto-color-emoji` (the installer adds it).
- **Line endings**: scripts edited on Windows can get CRLF line endings and fail with
  `bad interpreter`. This repo forces LF via `.gitattributes`; if you copy files by hand run
  `sed -i 's/\r$//' pi/*.sh`.
- **The kiosk has no keyboard**: to load changed HTML, `sudo systemctl restart lightdm` or reboot.
- **Clock settings and the incognito browser**: kiosk Chromium runs incognito, so settings are saved
  through `server.py` to `web/clock_config.json`, not only in the browser.
- The cron scripts call `sudo` (backlight, restarting lightdm). The default Raspberry Pi OS user has
  passwordless sudo; if yours does not, allow those two commands in sudoers.

## Updating

```bash
cd ~/school-dashboard && git pull && sudo systemctl restart school-dashboard lightdm
```

or copy changed files from your computer:

```bash
scp web/dashboard.html <user>@<pi-address>:~/school-dashboard/web/
```

Re-run `sudo bash pi/install.sh` only when files in `pi/` changed.
