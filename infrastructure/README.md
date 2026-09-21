# Infrastructure Specification

## Overview

This document describes every AWS resource that will be created for the
**AWS Cloud Web Application** internship project.

Read this completely before running any AWS commands.

---

## AWS Resources to be Created

### 1. VPC (Virtual Private Cloud)
| Property | Value |
|---|---|
| Name | InternshipVPC |
| CIDR Block | 10.0.0.0/16 |
| DNS Hostnames | Enabled |
| DNS Resolution | Enabled |
| Tag | Project=InternshipAWS, Env=Demo |

**Cost:** VPC itself is FREE. No charges for creating a VPC.

---

### 2. Public Subnet
| Property | Value |
|---|---|
| Name | InternshipPublicSubnet |
| CIDR Block | 10.0.1.0/24 |
| Availability Zone | First AZ in your region (e.g. us-east-1a) |
| Auto-assign Public IPv4 | YES |
| Tag | Project=InternshipAWS, Env=Demo |

**Cost:** Subnets are FREE.

---

### 3. Internet Gateway
| Property | Value |
|---|---|
| Name | InternshipIGW |
| Attached to VPC | InternshipVPC |
| Tag | Project=InternshipAWS, Env=Demo |

**Cost:** Internet Gateway itself is FREE. Data transfer OUT costs apply after
Free Tier (first 100 GB/month free for EC2 → internet).

---

### 4. Route Table
| Property | Value |
|---|---|
| Name | InternshipPublicRT |
| VPC | InternshipVPC |
| Route | 0.0.0.0/0 → Internet Gateway |
| Subnet Association | InternshipPublicSubnet |
| Tag | Project=InternshipAWS, Env=Demo |

**Cost:** Route tables are FREE.

---

### 5. Security Group
| Property | Value |
|---|---|
| Name | InternshipWebSG |
| VPC | InternshipVPC |
| Inbound SSH | TCP 22 → Your IP ONLY |
| Inbound HTTP | TCP 80 → 0.0.0.0/0 |
| Outbound | All traffic → 0.0.0.0/0 |
| Tag | Project=InternshipAWS, Env=Demo |

**Cost:** Security groups are FREE.

---

### 6. IAM Resources
| Resource | Name | Purpose |
|---|---|---|
| IAM Group | InternDevelopers | Group for developer IAM users |
| IAM Group | CloudOperators | Group for operations IAM users |
| IAM User | aws-project-user | Project administration user |
| IAM Role | InternshipEC2S3Role | Role attached to EC2 instance |
| IAM Policy | InternshipS3BucketPolicy | Least-privilege S3 access policy |

**Cost:** IAM is FREE (no charge per user/role/policy).

---

### 7. EC2 Instance
| Property | Value |
|---|---|
| Name | InternshipWebServer |
| AMI | Ubuntu Server 22.04 LTS (Free Tier eligible) |
| Instance Type | t3.micro |
| Key Pair | Create new — NEVER commit the .pem file |
| VPC | InternshipVPC |
| Subnet | InternshipPublicSubnet |
| Auto-assign IP | Yes |
| Security Group | InternshipWebSG |
| IAM Role | InternshipEC2S3Role |
| EBS Volume | 8 GB gp3 (Free Tier: 30 GB total) |
| Tag | Project=InternshipAWS, Env=Demo |

**Cost:**
- Verify your Free Tier status at **AWS Billing → Free Tier** before launching.
- Always verify current AWS Free Tier eligibility and pricing in the AWS Billing and Cost Management console.

---

### 8. S3 Bucket
| Property | Value |
|---|---|
| Name | internship-aws-YOURNAME-2026 (must be globally unique) |
| Region | Same as EC2 |
| Access | PRIVATE (Block all public access = ON) |
| Versioning | Disabled (keeps costs low) |
| Folders | assets/, logs/, dataset/, backup/ |
| Tag | Project=InternshipAWS, Env=Demo |

**Cost:**
- Free Tier: 5 GB standard storage, 20,000 GET requests, 2,000 PUT requests
  per month for 12 months.
- Keep total stored objects small.

---

### 9. CloudWatch Alarms
| Alarm | Metric | Threshold | Period |
|---|---|---|---|
| InternshipCPUAlarm | CPUUtilization | > 70% | 5 min |
| InternshipStatusAlarm | StatusCheckFailed | >= 1 | 5 min |

**Cost:**
- Free Tier: 10 alarm-metrics per month FREE.
- Standard resolution alarms: FREE for first 10.
- This project uses 2 alarms — within Free Tier.

---

### 10. SNS Topic
| Property | Value |
|---|---|
| Name | InternshipAWSAlerts |
| Type | Standard |
| Protocol | Email |
| Endpoint | Your email address |

**Cost:**
- First 1 million SNS publishes FREE per month.
- 1,000 email deliveries FREE per month.
- This project is well within free limits.

---

### 11. EBS Snapshot
| Property | Value |
|---|---|
| Source Volume | EC2 root volume (8 GB) |
| Name | InternshipRootSnapshot |
| Tag | Project=InternshipAWS, Env=Demo |

**Cost:**
- EBS snapshot storage: $0.05 per GB/month.
- An 8 GB snapshot ≈ $0.40/month.
- **Delete the snapshot after demonstration to avoid ongoing charges.**
- Free Tier does NOT include EBS snapshots.

---

### 12. AWS Budget
| Alert | Threshold | Type |
|---|---|---|
| Budget Alert 1 | $1.00 | Actual cost |
| Budget Alert 2 | $3.00 | Actual cost |

**Cost:** First 2 budgets are FREE. Additional budgets: $0.02/day each.

---

## Resources NOT Being Created (Cost Safety)

| Resource | Reason Not Created |
|---|---|
| NAT Gateway | Costs ~$32/month — not needed |
| Application Load Balancer | Costs money — not needed for single instance |
| RDS | Costs money — not needed |
| Auto Scaling Group | Not needed — single instance demo |
| Multiple EC2 instances | Costs money — using exactly 1 |
| ECS / EKS / Kubernetes | Far too expensive for demo |
| Multi-AZ | Costs extra — demo uses single AZ |
| Multiple EBS snapshots | Costs $0.05/GB/month each — keeping 1 |

---

## Deployment Order

Execute in this exact order to avoid dependency errors:

```
1.  IAM Policies
2.  IAM Groups
3.  IAM Users (attach to groups)
4.  IAM EC2 Role (attach policy)
5.  VPC
6.  Internet Gateway (attach to VPC)
7.  Public Subnet
8.  Route Table (add route, associate subnet)
9.  Security Group
10. S3 Bucket (create + configure)
11. EC2 Instance (launch with role + security group)
12. SNS Topic + Email Subscription
13. CloudWatch Alarms (requires EC2 instance ID)
14. EBS Snapshot (requires EC2 volume ID)
15. AWS Budget
```

> **CloudFormation CLI note — REQUIRED flag:**
> When deploying via AWS CLI, you **must** include `--capabilities CAPABILITY_NAMED_IAM`
> because this template creates IAM resources with custom names.
> Without this flag the CLI command will fail immediately with:
> `InsufficientCapabilities: Requires capabilities : [CAPABILITY_NAMED_IAM]`
>
> ```bash
> aws cloudformation create-stack \
>   --stack-name InternshipAWSStack \
>   --template-body file://infrastructure/cloudformation-stack.yaml \
>   --parameters ... \
>   --capabilities CAPABILITY_NAMED_IAM \
>   --region us-east-1
> ```
>
> When using the AWS Console, check the acknowledgement box at the bottom of the
> review page: *"I acknowledge that AWS CloudFormation might create IAM resources
> with custom names."*

---

## Security Model Summary

1. **No hardcoded credentials** — EC2 uses IAM Instance Role exclusively.
2. **SSH restricted** — TCP 22 open to your IP only, not 0.0.0.0/0.
3. **Least privilege** — EC2 role only has access to the project S3 bucket.
4. **S3 private** — All public access blocked.
5. **No root credentials used** — IAM user for normal administration.
6. **Key pair .pem file** — Never committed to git (protected by .gitignore).

---

## Post-Deployment: Confirm SNS Email Subscription

> **This step is mandatory.** CloudWatch alarms will not send emails until
> the subscription is confirmed.

After the CloudFormation stack reaches `CREATE_COMPLETE`:

1. Check your email inbox for a message from **no-reply@sns.amazonaws.com**
2. Subject: **"AWS Notification - Subscription Confirmation"**
3. Click **"Confirm subscription"** in the email body
4. AWS opens a browser page: **"Subscription confirmed!"**

If you do not confirm within 3 days, the subscription expires and must be
re-created. Verify subscription status:
```bash
aws sns list-subscriptions \
  --query "Subscriptions[?contains(TopicArn,'InternshipAWSAlerts')].{Protocol:Protocol,Status:SubscriptionArn}"
```
Status should show a full ARN (not `PendingConfirmation`).

---

## Cost Risk Summary

| Risk Level | Resource | Action |
|---|---|---|
| LOW | EBS Snapshot | Delete after demo |
| LOW | EC2 (t3.micro) | Stop when not demonstrating |
| LOW | S3 | Keep objects minimal |
| NONE | VPC/Subnet/IGW/RT/SG | Free |
| NONE | IAM | Free |
| NONE | CloudWatch Alarms (2) | Within free tier |
| NONE | SNS (email) | Within free tier |
| NONE | Budgets (2) | Free |

**Estimated monthly cost within Free Tier: $0.00–$0.50**
(Snapshot is the only resource outside Free Tier — delete it after demo.)
