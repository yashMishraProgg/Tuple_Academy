#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  Tuple Academy — AWS Lightsail Ubuntu Deployment Script
#  Stack: Ubuntu 22.04 + Python + Gunicorn + Caddy
#  Run this script ON YOUR LIGHTSAIL SERVER as root or with sudo
#  Usage: sudo bash deploy.sh
# ═══════════════════════════════════════════════════════════════

set -e  # stop on any error

# ── CHANGE THESE BEFORE RUNNING ───────────────────────────────
DOMAIN="tupleacademy.in"          # your domain name
APP_DIR="/var/www/tuple_academy"   # where app will live
APP_USER="tupleapp"               # linux user to run the app
SECRET_KEY="change-this-to-a-long-random-secret-key-2025"
# ──────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Tuple Academy — Lightsail Setup        ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── STEP 1: Update system ──────────────────────────────────────
echo "▶ Step 1: Updating system packages..."
apt-get update -y
apt-get upgrade -y
apt-get install -y python3 python3-pip python3-venv git curl unzip

# ── STEP 2: Create app user ────────────────────────────────────
echo "▶ Step 2: Creating app user '$APP_USER'..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
    echo "  ✓ User $APP_USER created"
else
    echo "  ✓ User $APP_USER already exists"
fi

# ── STEP 3: Create app directory ──────────────────────────────
echo "▶ Step 3: Creating app directory..."
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/instance"
mkdir -p "$APP_DIR/static/uploads"
mkdir -p "/var/log/tuple_academy"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
chown -R "$APP_USER":"$APP_USER" "/var/log/tuple_academy"
echo "  ✓ Directories created at $APP_DIR"

# ── STEP 4: Copy app files ─────────────────────────────────────
echo "▶ Step 4: Copying app files..."
# Copy from current directory (where you uploaded your files)
cp -r ./* "$APP_DIR/"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"
echo "  ✓ Files copied to $APP_DIR"

# ── STEP 5: Python virtual environment ────────────────────────
echo "▶ Step 5: Setting up Python virtual environment..."
cd "$APP_DIR"
sudo -u "$APP_USER" python3 -m venv venv
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install flask gunicorn werkzeug
echo "  ✓ Virtual environment ready"

# ── STEP 6: Environment file ───────────────────────────────────
echo "▶ Step 6: Creating environment file..."
cat > "$APP_DIR/.env" << EOF
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
EOF
chown "$APP_USER":"$APP_USER" "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"
echo "  ✓ .env file created"

# ── STEP 7: Install Caddy ──────────────────────────────────────
echo "▶ Step 7: Installing Caddy web server..."
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update -y
apt-get install -y caddy
echo "  ✓ Caddy installed"

# ── STEP 8: Caddy config ───────────────────────────────────────
echo "▶ Step 8: Configuring Caddy..."
cat > /etc/caddy/Caddyfile << EOF
$DOMAIN, www.$DOMAIN {
    reverse_proxy 127.0.0.1:8000

    # Security headers
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        X-XSS-Protection "1; mode=block"
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        -Server
    }

    # Static files served directly by Caddy (faster)
    handle /static/* {
        root * $APP_DIR
        file_server
    }

    # Logs
    log {
        output file /var/log/tuple_academy/caddy.log
        format json
    }
}
EOF
echo "  ✓ Caddyfile written"

# ── STEP 9: Gunicorn systemd service ──────────────────────────
echo "▶ Step 9: Creating Gunicorn systemd service..."
cat > /etc/systemd/system/tuple_academy.service << EOF
[Unit]
Description=Tuple Academy Flask App (Gunicorn)
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 3 \\
    --bind 127.0.0.1:8000 \\
    --timeout 120 \\
    --access-logfile /var/log/tuple_academy/access.log \\
    --error-logfile /var/log/tuple_academy/error.log \\
    --log-level info \\
    app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
echo "  ✓ Systemd service created"

# ── STEP 10: Start services ────────────────────────────────────
echo "▶ Step 10: Starting services..."
systemctl daemon-reload
systemctl enable tuple_academy
systemctl start tuple_academy
systemctl enable caddy
systemctl restart caddy
echo "  ✓ Gunicorn service started"
echo "  ✓ Caddy started"

# ── STEP 11: Firewall ──────────────────────────────────────────
echo "▶ Step 11: Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable
echo "  ✓ Firewall configured (22, 80, 443 open)"

# ── DONE ──────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         ✅ DEPLOYMENT COMPLETE           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  App directory : $APP_DIR"
echo "  App user      : $APP_USER"
echo "  Domain        : https://$DOMAIN"
echo "  Gunicorn port : 127.0.0.1:8000"
echo ""
echo "  Useful commands:"
echo "  → Check app status : sudo systemctl status tuple_academy"
echo "  → View app logs    : sudo journalctl -u tuple_academy -f"
echo "  → Restart app      : sudo systemctl restart tuple_academy"
echo "  → Check caddy      : sudo systemctl status caddy"
echo "  → View access logs : sudo tail -f /var/log/tuple_academy/access.log"
echo ""
echo "  ⚠  Make sure your domain DNS A record points to this server IP"
echo "  ⚠  Caddy will auto-get SSL certificate once DNS is pointed"
echo ""