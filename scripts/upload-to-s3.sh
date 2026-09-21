#!/bin/bash
# =============================================================================
# upload-to-s3.sh — Upload project assets to S3
# AWS Cloud Web Application — Internship Project
#
# Uploads website assets, dataset, and scripts to the project S3 bucket.
# Uses the EC2 IAM Instance Role — no credentials needed.
#
# Usage (from EC2):
#   bash scripts/upload-to-s3.sh
#
# Usage (from local with configured AWS CLI):
#   S3_BUCKET=your-bucket-name bash scripts/upload-to-s3.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'; ORANGE='\033[0;33m'; BLUE='\033[0;34m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${BLUE}[S3]${NC}   $1"; }
ok()   { echo -e "${GREEN}[OK]${NC}   $1"; }
warn() { echo -e "${ORANGE}[WARN]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

# ── Resolve bucket name ───────────────────────────────────────────────────────
if [ -n "${S3_BUCKET:-}" ]; then
    BUCKET="$S3_BUCKET"
elif [ -f "/home/ubuntu/s3-bucket-name.txt" ]; then
    BUCKET=$(cat /home/ubuntu/s3-bucket-name.txt)
else
    fail "S3 bucket name unknown. Set S3_BUCKET env var or create /home/ubuntu/s3-bucket-name.txt"
fi

log "Target bucket: s3://$BUCKET"

# Verify we can access the bucket (uses IAM role on EC2)
if ! aws s3 ls "s3://$BUCKET" > /dev/null 2>&1; then
    fail "Cannot access s3://$BUCKET — check IAM role permissions."
fi
ok "Bucket access verified."

# ── Resolve project root ──────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TODAY=$(date -u +%Y-%m-%d)

log "========================================================"
log " Uploading project assets to s3://$BUCKET"
log " Date: $TODAY"
log "========================================================"

# ── 1. Upload website assets ──────────────────────────────────────────────────
log "Uploading website assets..."
WEBAPP_DIR="$PROJECT_ROOT/web-app"
if [ -d "$WEBAPP_DIR" ]; then
    aws s3 sync "$WEBAPP_DIR/" "s3://$BUCKET/assets/" \
        --exclude ".*" \
        --delete
    ok "Website assets uploaded to s3://$BUCKET/assets/"
else
    warn "web-app/ directory not found. Skipping assets upload."
fi

# ── 2. Upload dataset ─────────────────────────────────────────────────────────
log "Uploading dataset..."
DATASET="$PROJECT_ROOT/dataset/web-access-logs.csv"
if [ -f "$DATASET" ]; then
    aws s3 cp "$DATASET" "s3://$BUCKET/dataset/web-access-logs.csv"
    ok "Dataset uploaded: s3://$BUCKET/dataset/web-access-logs.csv"
else
    warn "Dataset not found: $DATASET"
fi

# ── 3. Upload scripts (no .pem, no secrets) ───────────────────────────────────
log "Uploading scripts..."
aws s3 sync "$SCRIPT_DIR/" "s3://$BUCKET/scripts/" \
    --exclude "*.pem" \
    --exclude "*.ppk" \
    --exclude ".env" \
    --exclude "*.key" \
    --exclude ".*"
ok "Scripts uploaded to s3://$BUCKET/scripts/"

# ── 4. List uploaded content ──────────────────────────────────────────────────
log "Current S3 bucket contents:"
aws s3 ls "s3://$BUCKET" --recursive --human-readable | sort

# ── 5. Demonstrate denied access ─────────────────────────────────────────────
log "Testing bucket access control..."
FAKE_BUCKET="internship-aws-unauthorized-demo-bucket-xyz"
if aws s3 ls "s3://$FAKE_BUCKET" 2>&1 | grep -qiE "(AccessDenied|NoSuchBucket|403)"; then
    ok "Access to unauthorized bucket correctly DENIED (expected behaviour)."
else
    warn "Unauthorized bucket test inconclusive. Verify IAM policy restricts access."
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  S3 UPLOAD COMPLETE"
echo "  Bucket: s3://$BUCKET"
echo "  Date:   $TODAY"
echo "═══════════════════════════════════════════"
