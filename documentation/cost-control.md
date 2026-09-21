# Cost Control Documentation

## AWS Free Tier Strategy

This project is designed to stay within the AWS Free Tier.

> ⚠️ AWS Free Tier limits and eligibility can change. Always verify at:
> **AWS Billing → Free Tier** before creating resources.

### Free Tier Resources Used

| Resource | Free Tier Allowance | This Project |
|---|---|---|
| EC2 t3.micro | Verify current Free Tier eligibility at AWS Billing → Free Tier | 1 instance |
| EBS gp2/gp3 | 30 GB/month × 12 months | 8 GB |
| S3 Standard | 5 GB storage, 20K GET, 2K PUT × 12 months | Minimal |
| CloudWatch Alarms | 10 alarm-metrics/month | 2 alarms |
| SNS Email | 1,000 deliveries/month | ~10 test emails |
| CloudFormation | Always free | 1 stack |
| VPC/Subnet/IGW/RT/SG | Always free | 1 of each |
| IAM | Always free | Users/groups/roles |

### Resources Outside Free Tier

| Resource | Cost | Action |
|---|---|---|
| EBS Snapshot (8 GB) | $0.40/month | Delete after demo |
| Data transfer OUT | First 100 GB/month free | Demo traffic is minimal |

**Estimated monthly cost: $0.00 — $0.50**

---

## AWS Budgets Setup

Create two budget alerts to get early warning of any charges.

### Budget 1: $1 Alert

**Console:**
1. AWS Billing → Budgets → Create Budget
2. Budget type: **Cost budget**
3. Period: Monthly
4. Budget amount: $1.00
5. Alert threshold: 100% of actual spend
6. Email: your@email.com
7. Create budget

**CLI:**
```bash
aws budgets create-budget \
  --account-id YOUR-ACCOUNT-ID \
  --budget '{
    "BudgetName": "InternshipAWS-$1-Alert",
    "BudgetLimit": {"Amount": "1.00", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 100,
      "ThresholdType": "PERCENTAGE"
    },
    "Subscribers": [{
      "SubscriptionType": "EMAIL",
      "Address": "your@email.com"
    }]
  }]'
```

### Budget 2: $3 Alert

Repeat the above with `BudgetName: "InternshipAWS-$3-Alert"` and `Amount: "3.00"`.

**Cost of Budgets:**
- First 2 budgets: **FREE**
- Additional budgets: $0.02/day each

---

## Monitoring Free Tier Usage

Check your current Free Tier consumption:

```bash
# Check for services generating unexpected charges
aws ce get-cost-and-usage \
  --time-period "Start=2026-08-01,End=2026-09-01" \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE
```

Or in Console: **AWS Billing → Free Tier** → Shows current usage vs. limits.

---

## Resource Tagging

All resources are tagged for cost allocation and cleanup:

| Tag Key | Value |
|---|---|
| Project | InternshipAWS |
| Env | Demo |
| Owner | Your name |

These tags let you filter billing reports by project in:
**AWS Billing → Cost Explorer → Tag key: Project**

---

## Post-Demo Cleanup Procedure

Run in this exact order to avoid dependency errors.

### Step 1 — Delete EBS Snapshot
```bash
# List snapshots
aws ec2 describe-snapshots --filters "Name=tag:Project,Values=InternshipAWS" \
  --query "Snapshots[*].SnapshotId" --output text

# Delete (replace with actual snapshot ID)
aws ec2 delete-snapshot --snapshot-id snap-XXXXX
```

### Step 2 — Terminate EC2 Instance
```bash
aws ec2 terminate-instances --instance-ids YOUR-INSTANCE-ID
aws ec2 wait instance-terminated --instance-ids YOUR-INSTANCE-ID
```

### Step 3 — Empty and Delete S3 Bucket
```bash
# Empty the bucket first (CloudFormation cannot delete non-empty bucket)
aws s3 rm s3://YOUR-BUCKET-NAME --recursive

# Delete the bucket
aws s3api delete-bucket --bucket YOUR-BUCKET-NAME
```

### Step 4 — Delete CloudWatch Alarms
```bash
aws cloudwatch delete-alarms \
  --alarm-names \
    "InternshipAWS-CPUUtilizationAlarm" \
    "InternshipAWS-StatusCheckAlarm"
```

### Step 5 — Delete SNS Topic and Subscriptions
```bash
# List subscriptions
aws sns list-subscriptions-by-topic --topic-arn YOUR-SNS-ARN

# Delete subscription
aws sns unsubscribe --subscription-arn YOUR-SUBSCRIPTION-ARN

# Delete topic
aws sns delete-topic --topic-arn YOUR-SNS-ARN
```

### Step 6 — Delete CloudFormation Stack (cleans VPC/SG/IAM)

```bash
# Empty S3 bucket first (done in Step 3), then:
aws cloudformation delete-stack --stack-name InternshipAWSStack

# Wait for completion
aws cloudformation wait stack-delete-complete --stack-name InternshipAWSStack
echo "Stack deleted."
```

### Step 7 — Delete Key Pair
```bash
aws ec2 delete-key-pair --key-name internship-keypair
# Also delete the .pem file from your local machine
```

### Step 8 — Delete Budgets
AWS Billing → Budgets → Select both budgets → Delete

### Step 9 — Delete IAM Resources (if not using CloudFormation)
```bash
aws iam remove-role-from-instance-profile \
  --instance-profile-name InternshipInstanceProfile \
  --role-name InternshipEC2S3Role
aws iam delete-instance-profile --instance-profile-name InternshipInstanceProfile
aws iam detach-role-policy --role-name InternshipEC2S3Role \
  --policy-arn arn:aws:iam::ACCOUNT-ID:policy/InternshipS3BucketPolicy
aws iam delete-role --role-name InternshipEC2S3Role
aws iam delete-policy --policy-arn arn:aws:iam::ACCOUNT-ID:policy/InternshipS3BucketPolicy
```

### Step 10 — Verify No Resources Remain
```bash
# Check for any running EC2 instances
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running,stopped" \
  --query "Reservations[*].Instances[*].InstanceId"

# Check for any snapshots
aws ec2 describe-snapshots --owner-ids self --query "Snapshots[*].SnapshotId"

# Check billing dashboard
# AWS Console → Billing → Bills → Current month
```

After cleanup, your ongoing cost should drop to $0.00.
