#!/bin/bash
# =============================================================================
# backup-logs.sh — Archive Nginx access logs to S3
# AWS Cloud Web Application — Internship Project
#
# Compresses today's Nginx access log and uploads it to S3.
# Structure: s3://BUCKET/logs/YYYY-MM-DD/internship_access.log.gz
#
# Run via cron (example — daily at 23:55 UTC):
#   55 23 * * * /home/ubuntu/scripts/backup-logs.sh >> /var/log/internship/log-backup.log 2>&1
#
# Usage:
#   bash scripts/backup-logs.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'; ORANGE='\033[0;33m'; BLUE='\033[0;34m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${BLUE}[LOGS]${NC} $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}   $1"; }
warn() { echo -e "${ORANGE}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

TODAY=$(date -u +%Y-%m-%d)
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)

# ── Resolve bucket name ───────────────────────────────────────────────────────
if [ -n "${S3_BUCKET:-}" ]; then
    BUCKET="$S3_BUCKET"
elif [ -f "/home/ubuntu/s3-bucket-name.txt" ]; then
    BUCKET=$(cat /home/ubuntu/s3-bucket-name.txt)
else
    fail "Bucket name unknown. Set S3_BUCKET env var."
fi

LOG_FILE="/var/log/nginx/internship_access.log"
TMP_DIR="/tmp/log-backup-$$"
mkdir -p "$TMP_DIR"

log "========================================================"
log " Log Backup — $TODAY"
log " Bucket: s3://$BUCKET/logs/$TODAY/"
log "========================================================"

# ── Check log file exists ─────────────────────────────────────────────────────
if [ ! -f "$LOG_FILE" ]; then
    warn "Nginx access log not found: $LOG_FILE"
    warn "Nginx may not have received any requests yet."
    exit 0
fi

LOG_LINES=$(wc -l < "$LOG_FILE")
LOG_SIZE=$(du -sh "$LOG_FILE" | cut -f1)
log "Log file: $LOG_FILE ($LOG_LINES lines, $LOG_SIZE)"

if [ "$LOG_LINES" -eq 0 ]; then
    warn "Log file is empty. Nothing to archive."
    exit 0
fi

# ── Compress the log ──────────────────────────────────────────────────────────
ARCHIVE="$TMP_DIR/internship_access_${TIMESTAMP}.log.gz"
gzip -c "$LOG_FILE" > "$ARCHIVE"
ARCHIVE_SIZE=$(du -sh "$ARCHIVE" | cut -f1)
ok "Log compressed: $ARCHIVE ($ARCHIVE_SIZE)"

# ── Upload to S3 ──────────────────────────────────────────────────────────────
S3_PATH="s3://$BUCKET/logs/$TODAY/internship_access_${TIMESTAMP}.log.gz"
log "Uploading to $S3_PATH..."
aws s3 cp "$ARCHIVE" "$S3_PATH"
ok "Log uploaded: $S3_PATH"

# ── Upload a metadata manifest ────────────────────────────────────────────────
MANIFEST="$TMP_DIR/manifest.txt"
cat > "$MANIFEST" << EOF
InternshipAWS Log Archive Manifest
===================================
Date:         $TODAY
Timestamp:    $TIMESTAMP UTC
Source:       $LOG_FILE
Lines:        $LOG_LINES
Source size:  $LOG_SIZE
Archive:      $ARCHIVE_SIZE (gzip)
S3 path:      $S3_PATH
Instance:     $(curl -s --max-time 2 http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null || echo "unknown")
Region:       $(curl -s --max-time 2 http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null || echo "unknown")
EOF

aws s3 cp "$MANIFEST" "s3://$BUCKET/logs/$TODAY/manifest_${TIMESTAMP}.txt"
ok "Manifest uploaded."

# ── List today's logs in S3 ───────────────────────────────────────────────────
log "Today's archived logs in S3:"
aws s3 ls "s3://$BUCKET/logs/$TODAY/" || warn "No logs found for $TODAY yet."

# ── Cleanup temp files ────────────────────────────────────────────────────────
rm -rf "$TMP_DIR"
ok "Temp files cleaned up."

echo ""
echo "════════════════════════════════════════"
echo "  LOG BACKUP COMPLETE"
echo "  s3://$BUCKET/logs/$TODAY/"
echo "════════════════════════════════════════"
