# Deployment Guide

## Prerequisites

Before deploying, ensure you have:

1. **AWS Account** with Free Tier eligibility
2. **AWS CLI** installed and configured
3. **Python 3.8+** for running analysis scripts locally
4. **SSH client** (Terminal on Mac/Linux, PuTTY or Windows Terminal on Windows)
5. **Your public IP** from https://checkip.amazonaws.com

---

## Quick Start — Full Deployment in 15 Steps

### Step 1: Clone / download the project
```bash
# The project lives at D:\AWS\aws-cloud-web-application\
# Copy to your machine or work directly in this directory
```

### Step 2: Configure AWS CLI
```bash
aws configure
# AWS Access Key ID:     (your aws-project-user access key)
# AWS Secret Access Key: (your aws-project-user secret key)
# Default region:        us-east-1  (or your preferred region)
# Default output format: json
```

### Step 3: Create EC2 Key Pair
```bash
aws ec2 create-key-pair \
  --key-name internship-keypair \
  --query "KeyMaterial" \
  --output text > ~/internship-keypair.pem

# Secure the key file
chmod 400 ~/internship-keypair.pem
# NEVER commit this file to git
```

### Step 4: Find your public IP
```bash
curl https://checkip.amazonaws.com
# Note the IP — you'll use it as AdminSSHCIDR: YOUR.IP.HERE/32
```

### Step 5: Deploy CloudFormation Stack
```bash
aws cloudformation create-stack \
  --stack-name InternshipAWSStack \
  --template-body file://infrastructure/cloudformation-stack.yaml \
  --parameters \
    ParameterKey=OwnerName,ParameterValue=YourName \
    ParameterKey=S3BucketName,ParameterValue=internship-aws-yourname-2026 \
    ParameterKey=EC2KeyPairName,ParameterValue=internship-keypair \
    ParameterKey=AdminSSHCIDR,ParameterValue=YOUR.IP.HERE/32 \
    ParameterKey=NotificationEmail,ParameterValue=you@email.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Watch the stack build:
aws cloudformation wait stack-create-complete --stack-name InternshipAWSStack
echo "Stack created!"
```

### Step 6: Confirm SNS Email
Check your inbox for the AWS confirmation email and click the link.

### Step 7: Get the EC2 Public IP
```bash
EC2_IP=$(aws cloudformation describe-stacks \
  --stack-name InternshipAWSStack \
  --query "Stacks[0].Outputs[?OutputKey=='EC2PublicIP'].OutputValue" \
  --output text)
echo "EC2 IP: $EC2_IP"
```

### Step 8: Wait for UserData to complete (2–3 minutes)
The EC2 instance runs the bootstrap script automatically.
Wait about 3 minutes after stack creation, then:
```bash
# Quick connectivity test
curl -s -o /dev/null -w "%{http_code}" http://$EC2_IP/
# Expected: 200
```

### Step 9: SSH into EC2
```bash
ssh -i ~/internship-keypair.pem ubuntu@$EC2_IP
```

### Step 10: Deploy web application files
```bash
# Create target directory on EC2 first (SCP will fail without it)
ssh -i ~/internship-keypair.pem ubuntu@$EC2_IP "mkdir -p /tmp/webapp"

# Copy web app files from your local machine to EC2
scp -i ~/internship-keypair.pem web-app/* ubuntu@$EC2_IP:/tmp/webapp/

# Also copy scripts and dataset so setup-server.sh can find them
scp -i ~/internship-keypair.pem -r scripts dataset ubuntu@$EC2_IP:/home/ubuntu/project/
scp -i ~/internship-keypair.pem -r web-app ubuntu@$EC2_IP:/home/ubuntu/project/

# SSH in and deploy
ssh -i ~/internship-keypair.pem ubuntu@$EC2_IP
# Now on EC2:
sudo cp /tmp/webapp/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
sudo chmod -R 644 /var/www/html/
sudo find /var/www/html -type d -exec chmod 755 {} \;
```

> **Note on setup-server.sh:** The script uses `BASH_SOURCE[0]` to locate
> project files. Run it **directly on the instance** (not piped via SSH) after
> copying the project directory:
> ```bash
> bash /home/ubuntu/project/scripts/setup-server.sh
> ```

### Step 11: Upload dataset and scripts
```bash
# On EC2 (after SSH):
BUCKET=$(cat ~/s3-bucket-name.txt)
aws s3 cp /var/www/html/ s3://$BUCKET/assets/ --recursive
```

### Step 12: Run log backup script
```bash
# On EC2:
bash ~/scripts/backup-logs.sh
```

### Step 13: Create EBS Snapshot
```bash
# On EC2:
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
VOLUME_ID=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query "Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId" \
  --output text)
aws ec2 create-snapshot \
  --volume-id $VOLUME_ID \
  --description "InternshipRootSnapshot" \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Project,Value=InternshipAWS}]'
```

### Step 14: Configure AWS Budget
AWS Console → Billing → Budgets → Create Budget → $1 and $3 alerts.

### Step 15: Verify everything
```bash
# Website
curl http://$EC2_IP

# Health check
curl http://$EC2_IP/health

# S3 access
aws s3 ls s3://YOUR-BUCKET/

# CloudWatch alarms
aws cloudwatch describe-alarms --alarm-name-prefix "InternshipAWS"

# Log analysis
python scripts/analyze_logs.py
```

---

## Troubleshooting Common Issues

### Cannot SSH into EC2
1. Check your current IP: `curl https://checkip.amazonaws.com`
2. Update security group if your IP has changed:
   ```bash
   NEW_IP=$(curl -s https://checkip.amazonaws.com)
   aws ec2 authorize-security-group-ingress \
     --group-id YOUR-SG-ID \
     --protocol tcp --port 22 \
     --cidr "$NEW_IP/32"
   ```

### Website not loading (connection refused)
1. Verify EC2 is running: `aws ec2 describe-instances --instance-ids YOUR-ID`
2. Check Nginx is running: `sudo systemctl status nginx`
3. Check security group allows port 80

### S3 AccessDenied
1. Verify IAM role is attached to EC2 instance
2. Verify the bucket name in the IAM policy matches exactly
3. Check: `aws sts get-caller-identity` — should show the role ARN

### CloudFormation stack stuck
Check events:
```bash
aws cloudformation describe-stack-events \
  --stack-name InternshipAWSStack \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED']"
```

---

## Post-Demo Cleanup

Run these steps **after your internship demonstration** to stop all AWS charges.

### Step 1 — Delete EBS snapshot (only chargeable item outside Free Tier)
```bash
# Find snapshot ID
aws ec2 describe-snapshots --owner-ids self \
  --filters "Name=tag:Project,Values=InternshipAWS" \
  --query "Snapshots[*].SnapshotId" --output text

# Delete it
aws ec2 delete-snapshot --snapshot-id snap-XXXXXXXXXXXXXXXXX
```

### Step 2 — Empty the S3 bucket (required before stack deletion)
```bash
aws s3 rm s3://YOUR-BUCKET-NAME --recursive
```

### Step 3 — Delete the CloudFormation stack
This removes EC2, VPC, security group, IAM role, S3 bucket, SNS topic,
CloudWatch alarms, and all related resources in one command.
```bash
aws cloudformation delete-stack --stack-name InternshipAWSStack
aws cloudformation wait stack-delete-complete --stack-name InternshipAWSStack
echo "Stack deleted successfully."
```

### Step 4 — Delete budgets (optional — budgets are free, but keep things tidy)
AWS Console → Billing → Budgets → select both → Delete.

### Step 5 — Delete key pair
```bash
aws ec2 delete-key-pair --key-name internship-keypair
# Also delete the .pem file from your local machine
rm -i ~/internship-keypair.pem
```

### Step 6 — Verify nothing remains
```bash
# Check for running instances
aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running,stopped" \
  --query "Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key=='Project'].Value|[0]]" \
  --output table

# Check for leftover snapshots
aws ec2 describe-snapshots --owner-ids self \
  --query "Snapshots[*].[SnapshotId,Description]" --output table

# Check monthly cost so far
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY --metrics BlendedCost \
  --query "ResultsByTime[0].Total.BlendedCost"
```
