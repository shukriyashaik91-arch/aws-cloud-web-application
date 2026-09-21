# Screenshot & Evidence Checklist

## For Your Internship Submission

Take each screenshot listed below. File name suggestions are given.
⚠️ NEVER include passwords, access keys, or account IDs in screenshots.
   You may blur/crop those values before submission.

---

## IAM Screenshots

### SS-01: IAM User
**Where:** IAM → Users → aws-project-user
**What to show:** Username, groups, creation date
**File name:** `SS-01-IAM-user-aws-project-user.png`
- [ ] Captured

### SS-02: IAM Groups
**Where:** IAM → Groups
**What to show:** Both groups: InternDevelopers and CloudOperators
**File name:** `SS-02-IAM-groups.png`
- [ ] Captured

### SS-03: IAM Role
**Where:** IAM → Roles → InternshipAWS-EC2S3Role
**What to show:** Role name, trusted entity (EC2), attached policies
**File name:** `SS-03-IAM-role-EC2S3.png`
- [ ] Captured

### SS-04: IAM Policy
**Where:** IAM → Policies → InternshipS3BucketPolicy → JSON tab
**What to show:** The policy JSON with s3:GetObject, s3:PutObject, s3:ListBucket
and the specific bucket ARN (blur account ID if visible)
**File name:** `SS-04-IAM-policy-S3.png`
- [ ] Captured

---

## VPC / Networking Screenshots

### SS-05: VPC
**Where:** VPC → Your VPCs → InternshipAWS-VPC
**What to show:** VPC ID, CIDR 10.0.0.0/16, DNS hostnames enabled
**File name:** `SS-05-VPC.png`
- [ ] Captured

### SS-06: Public Subnet
**Where:** VPC → Subnets → InternshipAWS-PublicSubnet
**What to show:** Subnet CIDR 10.0.1.0/24, "Auto-assign public IPv4" enabled
**File name:** `SS-06-public-subnet.png`
- [ ] Captured

### SS-07: Internet Gateway
**Where:** VPC → Internet Gateways → InternshipAWS-IGW
**What to show:** Gateway name, State: Attached, VPC attachment
**File name:** `SS-07-internet-gateway.png`
- [ ] Captured

### SS-08: Route Table
**Where:** VPC → Route Tables → InternshipAWS-PublicRT → Routes tab
**What to show:** Two routes: local (10.0.0.0/16) and 0.0.0.0/0 → IGW
**File name:** `SS-08-route-table.png`
- [ ] Captured

### SS-09: Security Group
**Where:** EC2 → Security Groups → InternshipAWS-WebSG → Inbound rules
**What to show:** Port 22 → your IP, Port 80 → 0.0.0.0/0
(blur your actual IP address)
**File name:** `SS-09-security-group.png`
- [ ] Captured

---

## EC2 Screenshots

### SS-10: EC2 Instance
**Where:** EC2 → Instances → InternshipAWS-WebServer
**What to show:** Instance state: Running, instance type t3.micro, public IP,
IAM role attached
**File name:** `SS-10-EC2-instance.png`
- [ ] Captured

---

## Website Screenshots

### SS-11: Running Website — Home Page
**Where:** Browser → http://EC2-PUBLIC-IP
**What to show:** Full home page with hero section, AWS service cards
**File name:** `SS-11-website-home.png`
- [ ] Captured

### SS-12: Website — Services Section
**Where:** Browser → scroll to AWS Services section
**What to show:** Service cards for VPC, EC2, S3, IAM, etc.
**File name:** `SS-12-website-services.png`
- [ ] Captured

### SS-13: Website — Architecture Diagram
**Where:** Browser → scroll to Architecture section
**What to show:** The architecture flow diagrams
**File name:** `SS-13-website-architecture.png`
- [ ] Captured

### SS-14: Health Endpoint
**Where:** Browser → http://EC2-PUBLIC-IP/health
**What to show:** "Application Status: Healthy" with metric table
**File name:** `SS-14-health-endpoint.png`
- [ ] Captured

---

## S3 Screenshots

### SS-15: S3 Bucket
**Where:** S3 → Buckets → Your bucket
**What to show:** Bucket name, region, "Objects" tab with folders
**File name:** `SS-15-S3-bucket.png`
- [ ] Captured

### SS-16: S3 Objects
**Where:** S3 → Bucket → Browse each folder
**What to show:** assets/ folder, dataset/ folder, logs/ folder
**File name:** `SS-16-S3-objects.png`
- [ ] Captured

### SS-17: S3 Public Access Block
**Where:** S3 → Bucket → Permissions → Block public access
**What to show:** All four checkboxes = ON (green)
**File name:** `SS-17-S3-public-access-blocked.png`
- [ ] Captured

---

## Monitoring Screenshots

### SS-18: CloudWatch Alarms List
**Where:** CloudWatch → Alarms → All alarms
**What to show:** Both InternshipAWS alarms with state (OK or ALARM)
**File name:** `SS-18-CloudWatch-alarms.png`
- [ ] Captured

### SS-19: CloudWatch CPU Alarm Detail
**Where:** CloudWatch → Alarms → CPU alarm → Details
**What to show:** Alarm name, metric, threshold 70%, SNS action
**File name:** `SS-19-CloudWatch-CPU-alarm.png`
- [ ] Captured

### SS-20: CloudWatch CPU Metric Graph
**Where:** CloudWatch → Metrics → EC2 → CPUUtilization (your instance)
**What to show:** Graph of CPU over time
**File name:** `SS-20-CloudWatch-CPU-graph.png`
- [ ] Captured

### SS-21: SNS Email Confirmation
**Where:** Your email inbox — "AWS Notification - Subscription Confirmation" or test email
**What to show:** Email with "Subscription confirmed" or test alert received
(blur your email address)
**File name:** `SS-21-SNS-email-notification.png`
- [ ] Captured

### SS-22: SNS Topic
**Where:** SNS → Topics → InternshipAWSAlerts
**What to show:** Topic name, ARN, subscriptions count
**File name:** `SS-22-SNS-topic.png`
- [ ] Captured

---

## Backup Screenshot

### SS-23: EBS Snapshot
**Where:** EC2 → Snapshots → Your snapshot
**What to show:** Snapshot ID, Status: Completed, Size: 8 GiB, Description
**File name:** `SS-23-EBS-snapshot.png`
- [ ] Captured

---

## AWS Budget Screenshot

### SS-24: AWS Budget
**Where:** AWS Billing → Budgets
**What to show:** Both budget alerts ($1 and $3) configured
**File name:** `SS-24-AWS-budgets.png`
- [ ] Captured

---

## Log Analysis Screenshot

### SS-25: Log Analysis Output
**Where:** Terminal / Command Prompt — after running `python scripts/analyze_logs.py`
**What to show:** Full output with all 8 metrics visible
**File name:** `SS-25-log-analysis-output.png`
- [ ] Captured

---

## Checklist Summary

```
IAM
[ ] SS-01 IAM User
[ ] SS-02 IAM Groups
[ ] SS-03 IAM Role
[ ] SS-04 IAM Policy

VPC / NETWORKING
[ ] SS-05 VPC
[ ] SS-06 Public Subnet
[ ] SS-07 Internet Gateway
[ ] SS-08 Route Table
[ ] SS-09 Security Group

EC2
[ ] SS-10 EC2 Instance

WEBSITE
[ ] SS-11 Home Page
[ ] SS-12 Services Section
[ ] SS-13 Architecture Diagram
[ ] SS-14 Health Endpoint

S3
[ ] SS-15 S3 Bucket
[ ] SS-16 S3 Objects
[ ] SS-17 S3 Public Access Blocked

MONITORING
[ ] SS-18 CloudWatch Alarms List
[ ] SS-19 CloudWatch CPU Alarm Detail
[ ] SS-20 CloudWatch CPU Graph
[ ] SS-21 SNS Email Notification
[ ] SS-22 SNS Topic

BACKUP
[ ] SS-23 EBS Snapshot

COST
[ ] SS-24 AWS Budget

LOG ANALYSIS
[ ] SS-25 Log Analysis Output

TOTAL: 25 screenshots
```
