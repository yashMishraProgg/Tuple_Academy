#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Tuple Academy — Update Script
#  Run this whenever you push new code changes
#  Usage: sudo bash update.sh
# ═══════════════════════════════════════════════════════════════

APP_DIR="/var/www/tuple_academy"
APP_USER="tupleapp"

echo ""
echo "▶ Copying new files..."
cp -r ./* "$APP_DIR/"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

echo "▶ Installing any new dependencies..."
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "▶ Restarting Gunicorn..."
systemctl restart tuple_academy

echo ""
echo "✅ Update complete!"
echo "→ Check status: sudo systemctl status tuple_academy"
echo "→ View logs:    sudo journalctl -u tuple_academy -f"
echo ""