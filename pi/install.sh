#!/bin/bash
# Installs the school dashboard on a Raspberry Pi (Raspberry Pi OS with desktop, Bookworm or newer).
#   cd ~/school-dashboard && sudo bash pi/install.sh
# Safe to run again. Does not touch /boot/firmware/config.txt: screen settings are in docs/raspberry-pi.md.

set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="${SUDO_USER:-$(stat -c %U "$APP_DIR")}"
APP_HOME="$(getent passwd "$APP_USER" | cut -d: -f6)"
PI_DIR="$APP_DIR/pi"

if [ "$(id -u)" -ne 0 ]; then echo "Kör med sudo: sudo bash pi/install.sh"; exit 1; fi
echo "=== School dashboard: installerar i $APP_DIR för användaren $APP_USER ==="

echo "[1/6] Paket..."
apt-get update -qq
apt-get install -y -qq python3 python3-requests python3-dotenv chromium curl wlr-randr fonts-noto-color-emoji

echo "[2/6] Konfiguration..."
if [ ! -f "$APP_DIR/config.json" ]; then
  cp "$APP_DIR/config.example.json" "$APP_DIR/config.json"
  chown "$APP_USER:$APP_USER" "$APP_DIR/config.json"
  echo "  config.json skapad från exemplet (adapter: sample). Ändra den när du kopplat in riktig data."
fi
[ -f "$APP_DIR/.env" ] && chmod 600 "$APP_DIR/.env" && chown "$APP_USER:$APP_USER" "$APP_DIR/.env"

echo "[3/6] systemd-tjänster..."
for unit in school-dashboard.service school-fetch.service school-fetch.timer; do
  sed -e "s#__APP_DIR__#$APP_DIR#g" -e "s#__APP_USER__#$APP_USER#g" "$PI_DIR/$unit" > "/etc/systemd/system/$unit"
done
systemctl daemon-reload
systemctl enable --now school-dashboard.service school-fetch.timer

echo "[4/6] Hämtar data första gången..."
systemctl start school-fetch.service || echo "  [!] Hämtningen misslyckades: journalctl -u school-fetch -n 50"

echo "[5/6] Skärmschema och watchdog (cron var 5:e minut)..."
chmod +x "$PI_DIR"/*.sh
( crontab -u "$APP_USER" -l 2>/dev/null | grep -v -e screen-power.sh -e kiosk-watchdog.sh
  echo "*/5 * * * * $PI_DIR/screen-power.sh"
  echo "*/5 * * * * $PI_DIR/kiosk-watchdog.sh" ) | crontab -u "$APP_USER" -

echo "[6/6] Kiosk-läge vid inloggning..."
mkdir -p "$APP_HOME/.config/autostart"
sed "s#__APP_DIR__#$APP_DIR#g" "$PI_DIR/kiosk.desktop" > "$APP_HOME/.config/autostart/kiosk.desktop"
chown -R "$APP_USER:$APP_USER" "$APP_HOME/.config/autostart"

IP_ADDR=$(hostname -I | awk '{print $1}')
echo ""
echo "=== Klart! ==="
echo "  På Pi:n:        http://localhost:8080/dashboard.html"
echo "  I hemnätverket: http://${IP_ADDR}:8080/dashboard.html"
echo ""
echo "  Kontrollera att Pi:n loggar in automatiskt (sudo raspi-config > System > Auto Login),"
echo "  starta sedan om: sudo reboot"
echo ""
echo "  Status:     systemctl status school-dashboard school-fetch.timer"
echo "  Hämta nu:   sudo systemctl start school-fetch && journalctl -u school-fetch -n 20"
