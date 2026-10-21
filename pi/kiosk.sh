#!/bin/bash
# Opens the dashboard full screen. Started at login by ~/.config/autostart/kiosk.desktop.
sleep 5
for i in $(seq 1 30); do   # wait for the network (weather, fonts)
  ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1 && break
  sleep 2
done
for i in $(seq 1 15); do   # wait for server.py
  curl -s -o /dev/null http://localhost:8080/dashboard.html && break
  sleep 2
done
export WAYLAND_DISPLAY=wayland-0
export XDG_RUNTIME_DIR=/run/user/$(id -u)
chromium --kiosk --start-fullscreen --ozone-platform=wayland --noerrdialogs --disable-infobars \
  --disable-session-crashed-bubble --disable-restore-session-state --check-for-update-interval=31536000 \
  --disable-features=TranslateUI --password-store=basic --incognito 'http://localhost:8080/dashboard.html?kiosk=1'
