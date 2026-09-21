#!/bin/bash
# =============================================================================
# setup-server.sh — EC2 Server Setup and Web Application Deployment
# AWS Cloud Web Application — Internship Project
#
# Run this script on the EC2 instance after launch.
# It installs software, configures Nginx, and deploys the web application.
#
# Usage (run as ubuntu user on EC2):
#   bash setup-server.sh
#
# SECURITY:
#   - Does NOT contain any AWS credentials
#   - Does NOT open additional ports
#   - Uses IAM Instance Role for AWS CLI access
# =============================================================================

set -euo pipefail

# ── Colour output ─────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${BLUE}[SETUP]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}    $1"; }
warn() { echo -e "${ORANGE}[WARN]${NC}  $1"; }
fail() { echo -e "${RED}[FAIL]${NC}  $1"; exit 1; }

log "========================================================"
log " InternshipAWS — EC2 Server Setup Script"
log " $(date -u)"
log "========================================================"

# ── Resolve script and project paths ─────────────────────────────────────────
# BASH_SOURCE[0] is empty when the script is piped through stdin (bash -s < script.sh).
# Always run this script directly on the EC2 instance after copying the project:
#   bash /home/ubuntu/project/scripts/setup-server.sh
# Do NOT run it via: ssh host 'bash -s' < setup-server.sh
if [[ -z "${BASH_SOURCE[0]}" || "${BASH_SOURCE[0]}" == "-" ]]; then
    warn "Script appears to be running via stdin pipe. BASH_SOURCE is empty."
    warn "Path auto-detection will fall back to /home/ubuntu/project."
    warn "For reliable results, copy the project to EC2 and run directly:"
    warn "  bash /home/ubuntu/project/scripts/setup-server.sh"
    SCRIPT_DIR="/home/ubuntu/project/scripts"
    PROJECT_ROOT="/home/ubuntu/project"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
fi
log "Script dir : $SCRIPT_DIR"
log "Project root: $PROJECT_ROOT"

# ── Step 1: System update ─────────────────────────────────────────────────────
log "Step 1: Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y -q
ok "System updated."

# ── Step 2: Install required packages ─────────────────────────────────────────
log "Step 2: Installing Nginx, Python, AWS CLI..."
sudo apt-get install -y \
    nginx \
    python3 \
    python3-pip \
    awscli \
    curl \
    unzip

sudo systemctl enable nginx
sudo systemctl start nginx
ok "Nginx installed and running."

# ── Step 3: Configure Nginx ───────────────────────────────────────────────────
log "Step 3: Configuring Nginx..."

# Create log directory
sudo mkdir -p /var/log/internship

# Nginx server block configuration
sudo tee /etc/nginx/sites-available/internship > /dev/null << 'NGINXCONF'
server {
    listen 80;
    server_name _;
    root /var/www/html;
    index index.html;

    # Access log — required for log archival to S3
    access_log /var/log/nginx/internship_access.log;
    error_log  /var/log/nginx/internship_error.log;

    location / {
        try_files $uri $uri/ =404;
        autoindex off;
    }

    # Security headers
    add_header X-Content-Type-Options "nosniff";
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
}
NGINXCONF

# Enable the site and disable the default
sudo ln -sf /etc/nginx/sites-available/internship /etc/nginx/sites-enabled/internship
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
sudo nginx -t && ok "Nginx config valid." || fail "Nginx config invalid!"

sudo systemctl reload nginx
ok "Nginx configured."

# ── Step 4: Deploy web application ────────────────────────────────────────────
log "Step 4: Deploying web application..."

WEB_ROOT="/var/www/html"
WEBAPP_DIR="$PROJECT_ROOT/web-app"

if [ -d "$WEBAPP_DIR" ]; then
    sudo cp "$WEBAPP_DIR"/*.html "$WEB_ROOT/"
    sudo cp "$WEBAPP_DIR"/*.css  "$WEB_ROOT/"
    sudo cp "$WEBAPP_DIR"/*.js   "$WEB_ROOT/"
    ok "Web application files deployed from $WEBAPP_DIR"
else
    warn "web-app/ directory not found at $WEBAPP_DIR"
    warn "Manually copy web-app/ files to $WEB_ROOT after setup."

    # Create a placeholder index.html so Nginx returns 200
    sudo tee "$WEB_ROOT/index.html" > /dev/null << 'PLACEHOLDER'
<!DOCTYPE html>
<html>
<head><title>InternshipAWS</title></head>
<body>
<h1>AWS Cloud Web Application</h1>
<p>Server is running. Deploy web-app files to complete setup.</p>
</body>
</html>
PLACEHOLDER
fi

# Set correct ownership and permissions
sudo chown -R www-data:www-data "$WEB_ROOT"
sudo chmod -R 644 "$WEB_ROOT"
sudo find "$WEB_ROOT" -type d -exec chmod 755 {} \;
ok "File permissions set."

# ── Step 5: Deploy scripts to EC2 ─────────────────────────────────────────────
log "Step 5: Deploying scripts..."

SCRIPTS_DEST="/home/ubuntu/scripts"
mkdir -p "$SCRIPTS_DEST"

if [ -d "$PROJECT_ROOT/scripts" ]; then
    cp "$PROJECT_ROOT/scripts"/*.sh  "$SCRIPTS_DEST/" 2>/dev/null || true
    cp "$PROJECT_ROOT/scripts"/*.py  "$SCRIPTS_DEST/" 2>/dev/null || true
    chmod +x "$SCRIPTS_DEST"/*.sh 2>/dev/null || true
    ok "Scripts deployed to $SCRIPTS_DEST"
fi

# ── Step 6: Upload dataset to S3 ──────────────────────────────────────────────
log "Step 6: Uploading dataset to S3..."

S3_BUCKET_FILE="/home/ubuntu/s3-bucket-name.txt"
if [ -f "$S3_BUCKET_FILE" ]; then
    S3_BUCKET=$(cat "$S3_BUCKET_FILE")
    DATASET_SRC="$PROJECT_ROOT/dataset/web-access-logs.csv"
    if [ -f "$DATASET_SRC" ]; then
        aws s3 cp "$DATASET_SRC" "s3://$S3_BUCKET/dataset/web-access-logs.csv"
        ok "Dataset uploaded to s3://$S3_BUCKET/dataset/"
    else
        warn "Dataset file not found: $DATASET_SRC"
    fi
else
    warn "S3 bucket name file not found at $S3_BUCKET_FILE"
    warn "Set S3_BUCKET environment variable manually and upload with:"
    warn "  aws s3 cp dataset/web-access-logs.csv s3://YOUR-BUCKET/dataset/"
fi

# ── Step 7: Verify deployment ─────────────────────────────────────────────────
log "Step 7: Verifying deployment..."

# Check Nginx is running
if systemctl is-active --quiet nginx; then
    ok "Nginx is running."
else
    fail "Nginx is NOT running. Check: sudo systemctl status nginx"
fi

# Check HTTP response locally
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)
if [ "$HTTP_CODE" = "200" ]; then
    ok "Home page returns HTTP $HTTP_CODE"
else
    warn "Home page returned HTTP $HTTP_CODE (expected 200)"
fi

HTTP_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health.html)
if [ "$HTTP_HEALTH" = "200" ]; then
    ok "Health endpoint returns HTTP $HTTP_HEALTH"
else
    warn "Health endpoint returned HTTP $HTTP_HEALTH"
fi

# ── Step 8: Print EC2 instance info (no secrets) ──────────────────────────────
log "Step 8: Instance information..."

PUBLIC_IP=$(curl -s --max-time 3 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "unavailable")
INSTANCE_ID=$(curl -s --max-time 3 http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "unavailable")
REGION=$(curl -s --max-time 3 http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null || echo "unavailable")

echo ""
echo "═════════════════════════════════════════"
echo "  DEPLOYMENT COMPLETE"
echo "═════════════════════════════════════════"
echo "  Instance ID : $INSTANCE_ID"
echo "  Region      : $REGION"
echo "  Public IP   : $PUBLIC_IP"
echo "─────────────────────────────────────────"
echo "  Website     : http://$PUBLIC_IP"
echo "  Health      : http://$PUBLIC_IP/health"
echo "═════════════════════════════════════════"
echo ""
