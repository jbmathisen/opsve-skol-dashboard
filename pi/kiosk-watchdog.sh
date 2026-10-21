#!/bin/bash
# Self-heal: if the Pi is stuck at the login screen or the kiosk browser died, restart the display manager.
# Run every 5 min from the user's cron. Needs two failures in a row (~5 min apart) before acting.
# Assumes Raspberry Pi OS with the labwc (Wayland) desktop and lightdm, the default since Bookworm.

STATE=/tmp/kiosk-watchdog.fail

# Still booting (autologin + network wait + browser start can take a few minutes)
[ "$(cut -d. -f1 /proc/uptime)" -lt 300 ] && exit 0

if pgrep -x labwc >/dev/null && pgrep -f 'chromium.*--kiosk' >/dev/null; then
  rm -f "$STATE"
  exit 0
fi

if [ -f "$STATE" ]; then
  rm -f "$STATE"
  logger -t kiosk-watchdog "labwc or kiosk browser not running - restarting lightdm"
  sudo systemctl restart lightdm
else
  touch "$STATE"
fi
