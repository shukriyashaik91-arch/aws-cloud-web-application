# Testing Documentation

## Test Plan Overview

All tests are grouped by component. Run them in order after deployment.

---

## 1. Website Tests

### 1.1 Home Page Loads
**Test:** Open `http://EC2-PUBLIC-IP` in a browser.
**Expected:** Page loads with AWS Cloud Web Application portal.
**CLI test:**
```bash
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://EC2-PUBLIC-IP/
```
**Expected result:** `HTTP Status: 200`

### 1.2 Health Endpoint
**Test:** Open `http://EC2-PUBLIC-IP/health`
**Expected:** Page shows "Application Status: Healthy"
**CLI test:**
```bash
curl http://EC2-PUBLIC-IP/health
```
**Expected result:** HTML page with "Application Status: Healthy"

### 1.3 CSS Loads
```bash
curl -s -o /dev/null -w "%{http_code}" http://EC2-PUBLIC-IP/style.css
```
**Expected:** 200

### 1.4 JavaScript Loads
```bash
curl -s -o /dev/null -w "%{http_code}" http://EC2-PUBLIC-IP/script.js
```
**Expected:** 200

### 1.5 Directory Listing Disabled (Security)
```bash
curl -s -o /dev/null -w "%{http_code}" http://EC2-PUBLIC-IP/
```
**Expected:** 200 (index.html), NOT a directory listing.

---

## 2. Networking Tests

### 2.1 EC2 Has Internet Access
**On EC2 via SSH:**
```bash
curl -s https://aws.amazon.com | head -5
# Expected: HTML content (not "connection refused")
ping -c 3 8.8.8.8
```

### 2.2 SSH Restricted to Admin IP
**Test:** Attempt SSH from a different IP (e.g., a mobile hotspot).
**Expected:** Connection timeout or refused.
**Verify security group rule:**
```bash
aws ec2 describe-security-groups --group-names InternshipAWS-WebSG \
  --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`].IpRanges[0].CidrIp"
# Expected: YOUR.IP/32 — NOT 0.0.0.0/0
```

### 2.3 VPC and Subnet Exist
```bash
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=InternshipAWS" \
  --query "Vpcs[*].{ID:VpcId,CIDR:CidrBlock,Name:Tags[?Key=='Name'].Value|[0]}"
```
**Expected:** VPC with CIDR 10.0.0.0/16

---

## 3. IAM Tests

### 3.1 EC2 Uses IAM Role (Not Access Keys)
**On EC2:**
```bash
aws sts get-caller-identity
```
**Expected:**
```json
{
  "UserId": "AROAXXXXXXXXXX:i-xxxxxxxx",
  "Account": "123456789012",
  "Arn": "arn:aws:sts::123456789012:assumed-role/InternshipAWS-EC2S3Role/i-xxxxxxxx"
}
```
The ARN must contain `assumed-role/InternshipAWS-EC2S3Role` — NOT an IAM user ARN.

### 3.2 No Hardcoded Credentials in Code
```bash
# Search for common credential patterns in all project files
grep -r "AKIA"         . --include="*.py" --include="*.sh" --include="*.js"
grep -r "aws_secret"   . --include="*.py" --include="*.sh" --include="*.env"
grep -r "aws_access"   . --include="*.py" --include="*.sh" --include="*.env"
```
**Expected:** No matches found.

### 3.3 S3 Access Is Restricted
**On EC2:**
```bash
# This SHOULD succeed
aws s3 ls s3://YOUR-PROJECT-BUCKET
# Expected: lists bucket contents

# This SHOULD fail
aws s3 ls s3://amazon.com.backup.illegal.test.bucket.xyz
# Expected: An error occurred (AccessDenied) or NoSuchBucket
```

---

## 4. S3 Tests

### 4.1 Assets Uploaded
```bash
aws s3 ls s3://YOUR-BUCKET/assets/
# Expected: index.html, style.css, script.js, health.html
```

### 4.2 Dataset Uploaded
```bash
aws s3 ls s3://YOUR-BUCKET/dataset/
# Expected: web-access-logs.csv
```

### 4.3 Logs Archived
```bash
TODAY=$(date -u +%Y-%m-%d)
aws s3 ls s3://YOUR-BUCKET/logs/$TODAY/
# Expected: .log.gz file and manifest.txt
```

### 4.4 Bucket Is Private
```bash
# This should FAIL
curl -I https://YOUR-BUCKET.s3.amazonaws.com/
# Expected: 403 Forbidden or 307 redirect to error (never 200 with listing)

# Verify block public access
aws s3api get-public-access-block --bucket YOUR-BUCKET
# Expected: all four settings = true
```

---

## 5. Monitoring Tests

### 5.1 CloudWatch Alarms Exist
```bash
aws cloudwatch describe-alarms \
  --alarm-name-prefix "InternshipAWS" \
  --query "MetricAlarms[*].{Name:AlarmName,State:StateValue}"
```
**Expected:** 2 alarms in OK or INSUFFICIENT_DATA state.

### 5.2 SNS Topic Exists and Email is Confirmed
```bash
# List topic
aws sns list-topics --query "Topics[?contains(TopicArn,'InternshipAWSAlerts')]"

# Check subscription status
aws sns list-subscriptions \
  --query "Subscriptions[?contains(TopicArn,'InternshipAWSAlerts')].{Protocol:Protocol,Status:SubscriptionArn}"
# Expected: Status shows a subscription ARN (not PendingConfirmation)
```

### 5.3 Test Email Notification
```bash
SNS_ARN=$(aws sns list-topics \
  --query "Topics[?contains(TopicArn,'InternshipAWSAlerts')].TopicArn" --output text)
aws sns publish \
  --topic-arn "$SNS_ARN" \
  --subject "InternshipAWS — Monitoring Test" \
  --message "Test notification at $(date -u). Monitoring is working correctly."
```
**Expected:** Email arrives within 60 seconds.

---

## 6. Backup Tests

### 6.1 EBS Snapshot Exists
```bash
aws ec2 describe-snapshots \
  --filters "Name=tag:Project,Values=InternshipAWS" \
  --query "Snapshots[*].{ID:SnapshotId,State:State,Size:VolumeSize,Date:StartTime}"
```
**Expected:** At least 1 snapshot in Completed state.

---

## 7. Log Analysis Tests

### 7.1 Script Runs Successfully
```bash
python scripts/analyze_logs.py
```
**Expected:** Report prints without errors, shows all 8 metrics.

### 7.2 Correct Record Count
```bash
python scripts/analyze_logs.py --json | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print('Records:', d['total_requests'])"
```
**Expected:** `Records: 192`

### 7.3 All 8 Metrics Present in JSON Output
```bash
python scripts/analyze_logs.py --json | python3 -c "
import sys, json
d = json.load(sys.stdin)
required = ['total_requests','top_pages','errors_4xx','errors_5xx',
            'peak_traffic_hour','unique_visitor_ips',
            'most_common_method','average_response_size_bytes']
for key in required:
    status = '✅' if key in d else '❌ MISSING'
    print(f'{status} {key}')
"
```
**Expected:** All 8 metrics show ✅

### 7.4 CSV with Missing Data (Error Handling)
```bash
echo "timestamp,ip,method,path,status,bytes,user_agent
2026-08-01 09:00:00,1.2.3.4,GET,/,200,1234,curl
invalid-row,bad-data" | python3 -c "
import csv, sys, io
# Manually check the script handles bad rows gracefully
print('Error handling test: script should skip invalid rows, not crash')
"
python scripts/analyze_logs.py --csv /nonexistent/path.csv 2>&1 | head -3
```
**Expected:** Error message "CSV file not found" — no stack trace crash.

---

## 8. Cost Tests

### 8.1 AWS Budget Exists
AWS Console → Billing → Budgets → Verify 2 budgets configured.

### 8.2 No Expensive Resources Running
```bash
# Check for NAT Gateways (should be 0)
aws ec2 describe-nat-gateways \
  --filter "Name=state,Values=available" \
  --query "NatGateways[*].NatGatewayId"
# Expected: empty list []

# Check for Load Balancers (should be 0)
aws elbv2 describe-load-balancers \
  --query "LoadBalancers[*].LoadBalancerName"
# Expected: empty list []

# Verify exactly 1 running EC2 instance
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query "Reservations[*].Instances[*].InstanceId"
# Expected: exactly 1 instance ID
```

### 8.3 Resource Tags Applied
```bash
aws ec2 describe-instances \
  --filters "Name=tag:Project,Values=InternshipAWS" \
  --query "Reservations[*].Instances[*].Tags"
```
**Expected:** Tags include Project, Env, Owner, Name.

---

## Test Results Checklist

Copy this checklist and fill it in after completing all tests:

```
WEBSITE
[ ] Home page loads (HTTP 200)
[ ] Health page shows "Application Status: Healthy"
[ ] CSS loads correctly
[ ] JavaScript loads correctly

NETWORKING
[ ] EC2 has internet access
[ ] SSH restricted to admin IP only (NOT 0.0.0.0/0)
[ ] VPC exists with correct CIDR

IAM
[ ] EC2 uses IAM role (not access keys)
[ ] No credentials in source code
[ ] S3 access restricted to project bucket

S3
[ ] Assets uploaded to assets/
[ ] Dataset uploaded to dataset/
[ ] Logs archived to logs/YYYY-MM-DD/
[ ] Bucket is private (public access blocked)

MONITORING
[ ] 2 CloudWatch alarms exist
[ ] SNS subscription confirmed
[ ] Test email received successfully

BACKUP
[ ] EBS snapshot exists in Completed state
[ ] Restore procedure documented

LOG ANALYSIS
[ ] Script runs without errors
[ ] All 8 metrics shown correctly
[ ] JSON output works

COST
[ ] AWS Budget(s) configured
[ ] No NAT Gateway, ALB, or RDS found
[ ] Exactly 1 EC2 instance running
[ ] Resource tags applied
```
