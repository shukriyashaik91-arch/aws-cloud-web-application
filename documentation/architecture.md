# Architecture Documentation

## System Overview

The InternshipAWS project is a single-region, single-AZ cloud application
demonstrating core AWS services working together in a cost-controlled,
Free Tier-friendly architecture.

---

## Architecture Diagram

```
  Internet
     │
     │  HTTP :80
     ▼
┌──────────────────────────────────────────────────────┐
│  AWS Region (e.g. us-east-1)                         │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │  InternshipVPC  (10.0.0.0/16)               │    │
│  │                                             │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │  Public Subnet  (10.0.1.0/24)        │  │    │
│  │  │                                      │  │    │
│  │  │  ┌────────────────────────────────┐  │  │    │
│  │  │  │  EC2 t3.micro                  │  │  │    │
│  │  │  │  Ubuntu 22.04                  │  │  │    │
│  │  │  │  Nginx Web Server              │  │  │    │
│  │  │  │  IAM Role: EC2S3Role           │  │  │    │
│  │  │  │  EBS: 8 GB gp3                 │  │  │    │
│  │  │  └────────────────────────────────┘  │  │    │
│  │  │          │  Security Group           │  │    │
│  │  │          │  Port 22  → Admin IP      │  │    │
│  │  │          │  Port 80  → 0.0.0.0/0     │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                                             │    │
│  │  Route Table: 0.0.0.0/0 → IGW              │    │
│  └─────────────────────────────────────────────┘    │
│                  │                                   │
│         Internet Gateway                             │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  S3      │  │CloudWatch│  │  SNS             │  │
│  │ Private  │  │ Metrics  │  │ InternshipAlerts │  │
│  │ Bucket   │  │ Alarms   │  │ Email Notify     │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                      │
│  ┌──────────┐  ┌──────────┐                         │
│  │  IAM     │  │  EBS     │                         │
│  │ Roles    │  │ Snapshot │                         │
│  │ Policies │  │ Backup   │                         │
│  └──────────┘  └──────────┘                         │
└──────────────────────────────────────────────────────┘
```

---

## Component Descriptions

### VPC (10.0.0.0/16)
The Virtual Private Cloud creates an isolated network environment.
All resources in this project live inside this VPC.
The /16 CIDR provides 65,536 IP addresses — plenty for a demo.

### Public Subnet (10.0.1.0/24)
Houses the EC2 instance. "Public" means instances in this subnet
receive a public IP automatically and can route to/from the internet
via the Internet Gateway.

### Internet Gateway
The attachment point between the VPC and the internet.
The public route table sends all non-local traffic (0.0.0.0/0)
through the Internet Gateway.

### Route Table
Associates the public subnet with the IGW.
Route: `0.0.0.0/0 → igw-xxxxx`
Without this route, the EC2 instance cannot reach the internet.

### Security Group (InternshipWebSG)
A stateful firewall attached to the EC2 instance.
- Inbound TCP 22 → admin IP only (prevents brute-force)
- Inbound TCP 80 → 0.0.0.0/0 (public website)
- All other inbound ports: blocked
- All outbound: allowed (needed for apt updates, S3 access)

### EC2 Instance (t3.micro)
Single Linux web server running Nginx.
The IAM Instance Role gives it S3 access without hardcoded credentials.
The EBS root volume stores the OS, web server, and application.

### IAM Role (InternshipEC2S3Role)
Attached to the EC2 instance. Gives the instance permission to call
S3 APIs. No credentials are stored — AWS rotates temporary credentials
automatically via the instance metadata service.

### S3 Bucket
Private object storage for:
- `assets/` — HTML/CSS/JS backups
- `logs/YYYY-MM-DD/` — archived Nginx access logs
- `dataset/` — web-access-logs.csv for log analysis
- `backup/` — miscellaneous backup artefacts

Note: EBS snapshots are stored in AWS-managed snapshot storage, not in this S3 bucket.

### CloudWatch
AWS's monitoring service. Collects EC2 metrics every 5 minutes (free tier).
Creates alarms that evaluate metric data and trigger actions.

### SNS (InternshipAWSAlerts)
Message routing service. Receives alarm notifications from CloudWatch
and forwards them to the confirmed email subscriber.

### EBS Snapshot
Point-in-time backup of the EC2 root volume. Stored in AWS-managed S3.
Enables recovery if the EC2 instance is corrupted or terminated.

### AWS Budgets
Cost control. Sends email when actual monthly spend exceeds $1 or $3,
providing early warning before significant charges accumulate.

---

## Data Flow

### Web Request Flow
```
Browser → Internet → Internet Gateway → Route Table → Public Subnet
→ Security Group (port 80 allowed) → EC2 Nginx → HTML response
→ Security Group → Route Table → Internet Gateway → Browser
```

### Log Upload Flow
```
Nginx → /var/log/nginx/internship_access.log
→ backup-logs.sh (gzip compress)
→ AWS CLI (via IAM role)
→ S3: s3://bucket/logs/YYYY-MM-DD/
```

### Alarm Flow
```
EC2 → CPU metric → CloudWatch (5-min average) → Alarm evaluates
→ Threshold exceeded → SNS publish → Email delivery
```

### S3 Access Flow
```
EC2 application → AWS SDK/CLI
→ EC2 metadata service (169.254.169.254)
→ Temporary credentials from IAM role
→ S3 API → Bucket (authorized)
→ Any other bucket → AccessDenied (403)
```
