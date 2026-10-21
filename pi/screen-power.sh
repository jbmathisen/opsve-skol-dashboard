#!/bin/bash
# Screen schedule: bright during the day, dark at night. Run every 5 minutes from cron
# (idempotent, so it also self-corrects after reboots and power cuts).
# Times come from "screen" in config.json, the same values the dashboard uses to paint itself black.

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
read -r WEEKDAY_ON WEEKEND_ON OFF_TIME < <(python3 - "$APP_DIR" <<'PY'
import json, sys, pathlib
root = pathlib.Path(sys.argv[1])
cfg = root / "config.json"
if not cfg.exists():
    cfg = root / "config.example.json"
s = json.loads(cfg.read_text(encoding="utf-8")).get("screen", {})
print(s.get("weekday_on", "06:30"), s.get("weekend_on", "10:00"), s.get("off", "21:30"))
PY
)

export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/$(id -u)

# The Pi has no battery clock: right after a power cut the time is wrong until NTP syncs.
# Don't switch the screen based on a wrong time; leave it as is until the clock is right.
[ "$(timedatectl show -p NTPSynchronized --value)" = "yes" ] || exit 0

now=$(date +%H%M)
dow=$(date +%u)   # 1=Mon ... 7=Sun
if [ "$dow" -ge 6 ]; then on_time=$WEEKEND_ON; else on_time=$WEEKDAY_ON; fi
on_time=${on_time/:/}
off_time=${OFF_TIME/:/}

# Force base 10 (values like 0630 would otherwise be parsed as octal)
if [ $((10#$now)) -ge $((10#$on_time)) ] && [ $((10#$now)) -lt $((10#$off_time)) ]; then
  state="on"
else
  state="off"
fi

# The HDMI output is NEVER switched off: powering it down made some screens fail to wake up
# (black screen until reboot). At night dashboard.html paints itself black (kiosk mode) and here we
# only dim the backlight, if the screen exposes one. Always (re)enable outputs.
for out in $(wlr-randr | grep -E '^[A-Za-z]' | awk '{print $1}'); do
  wlr-randr --output "$out" --on
done

# Optional hardware backlight (official DSI touch screens have one, most HDMI screens don't:
# then set daytime brightness with the screen's own buttons; a black page at night is near-invisible).
for bl in /sys/class/backlight/*/; do
  [ -d "$bl" ] || continue
  max=$(cat "$bl/max_brightness")
  if [ "$state" = "on" ]; then val=$max; else val=0; fi
  echo "$val" | sudo tee "$bl/brightness" >/dev/null
done
