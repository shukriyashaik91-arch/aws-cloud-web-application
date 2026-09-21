# CloudFormation Deployment Guide

## Before You Start — Pre-flight Checklist

Run through every item before executing any AWS command.

- [ ] You have an AWS account (Free Tier recommended for new accounts)
- [ ] AWS CLI is installed: `aws --version`
- [ ] AWS CLI is configured: `aws configure` (use aws-project-user IAM user credentials)
- [ ] You have verified Free Tier status at **AWS Billing → Free Tier**
- [ ] You have noted your public IP: https://checkip.amazonaws.com
- [ ] You have an EC2 Key Pair created (EC2 → Key Pairs → Create)
- [ ] You have saved the .pem file securely (it will NOT be retrievable again)
- [ ] You have chosen a unique S3 bucket name

---

## Step 1 — Create the EC2 Key Pair (Console)

> Do this FIRST. You cannot add a key pair to a running instance.

1. AWS Console → EC2 → Key Pairs
2. Create Key Pair
3. Name: `internship-keypair`
4. Type: RSA
5. Format: .pem (Linux/Mac) or .ppk (PuTTY on Windows)
6. Download and save securely
7. **NEVER commit this file to git** — it is in .gitignore

---

## Step 2 — Deploy the CloudFormation Stack

### Option A — AWS Console (Recommended for beginners)

1. AWS Console → CloudFormation → Create Stack → With new resources
2. Template source: Upload a template file
3. Upload: `infrastructure/cloudformation-stack.yaml`
4. Click Next

**Fill in Parameters:**

| Parameter | Value to enter |
|---|---|
| Stack name | `InternshipAWSStack` |
| ProjectName | `InternshipAWS` |
| EnvironmentName | `Demo` |
| OwnerName | Your name |
| S3BucketName | `internship-aws-YOURNAME-2026` |
| EC2InstanceType | `t3.micro` |
| EC2KeyPairName | `internship-keypair` |
| AdminSSHCIDR | `YOUR.IP.ADDRESS.HERE/32` |
| NotificationEmail | `your@email.com` |

5. Tags page: add `Project=InternshipAWS`, `Env=Demo`
6. Permissions: leave default
7. **Check "I acknowledge that AWS CloudFormation might create IAM resources with custom names"**
8. Create Stack
9. Wait for `CREATE_COMPLETE` status (typically 3–5 minutes)

### Option B — AWS CLI

```bash
aws cloudformation create-stack \
  --stack-name InternshipAWSStack \
  --template-body file://infrastructure/cloudformation-stack.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=InternshipAWS \
    ParameterKey=EnvironmentName,ParameterValue=Demo \
    ParameterKey=OwnerName,ParameterValue=YourName \
    ParameterKey=S3BucketName,ParameterValue=internship-aws-yourname-2026 \
    ParameterKey=EC2InstanceType,ParameterValue=t3.micro \
    ParameterKey=EC2KeyPairName,ParameterValue=internship-keypair \
    ParameterKey=AdminSSHCIDR,ParameterValue=YOUR.IP.HERE/32 \
    ParameterKey=NotificationEmail,ParameterValue=you@email.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Check progress:
```bash
aws cloudformation describe-stacks \
  --stack-name InternshipAWSStack \
  --query "Stacks[0].StackStatus"
```

---

## Step 3 — Confirm SNS Email Subscription

After the stack creates:

1. Check your email inbox for a message from **AWS Notifications**
2. Subject: "AWS Notification - Subscription Confirmation"
3. Click **Confirm subscription**
4. You will see "Subscription confirmed!"

**This step is mandatory.** CloudWatch alarms will not send emails until
the subscription is confirmed.

---

## Step 4 — Get the EC2 Public IP

### Console
CloudFormation → Stacks → InternshipAWSStack → Outputs tab → EC2PublicIP

### CLI
```bash
aws cloudformation describe-stacks \
  --stack-name InternshipAWSStack \
  --query "Stacks[0].Outputs[?OutputKey=='EC2PublicIP'].OutputValue" \
  --output text
```

---

## Step 5 — Upload Web Application to EC2

SSH into the instance first:
```bash
ssh -i ~/path/to/internship-keypair.pem ubuntu@EC2-PUBLIC-IP
```

Then use the setup script (see scripts/setup-server.sh).
From your local machine:
```bash
# Create the target directory on EC2 first, then copy web app files
ssh -i ~/path/to/internship-keypair.pem ubuntu@EC2-PUBLIC-IP "mkdir -p /tmp/webapp"
scp -i ~/path/to/internship-keypair.pem \
    web-app/* \
    ubuntu@EC2-PUBLIC-IP:/tmp/webapp/

# SSH in and move files to web root
ssh -i ~/path/to/internship-keypair.pem ubuntu@EC2-PUBLIC-IP
sudo cp /tmp/webapp/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html/
```

> **Important:** Do NOT run setup-server.sh by piping it through SSH like
> `ssh ... 'bash -s' < setup-server.sh`. That makes `BASH_SOURCE[0]` empty
> and breaks the script's path resolution. Instead, copy the project files
> to EC2 first and run the script directly on the instance:
> ```bash
> # Copy the whole project to EC2
> scp -i ~/path/to/internship-keypair.pem -r \
>     web-app scripts dataset \
>     ubuntu@EC2-PUBLIC-IP:/home/ubuntu/project/
>
> # Then SSH in and run the script directly
> ssh -i ~/path/to/internship-keypair.pem ubuntu@EC2-PUBLIC-IP
> bash /home/ubuntu/project/scripts/setup-server.sh
> ```

---

## Step 6 — Verify the Application

```bash
# Test home page
curl -I http://EC2-PUBLIC-IP

# Test health endpoint
curl http://EC2-PUBLIC-IP/health

# Open in browser
http://EC2-PUBLIC-IP
http://EC2-PUBLIC-IP/health
```

Expected:
- Home page returns HTTP 200
- Health page shows "Application Status: Healthy"

---

## Step 7 — Upload Dataset to S3

```bash
# Get bucket name
BUCKET=$(cat /home/ubuntu/s3-bucket-name.txt)

# Upload dataset
aws s3 cp dataset/web-access-logs.csv s3://$BUCKET/dataset/web-access-logs.csv

# List to verify
aws s3 ls s3://$BUCKET/dataset/
```

---

## Updating the Stack

If you change the CloudFormation template:
```bash
aws cloudformation update-stack \
  --stack-name InternshipAWSStack \
  --template-body file://infrastructure/cloudformation-stack.yaml \
  --parameters ... \
  --capabilities CAPABILITY_NAMED_IAM
```

---

## Deleting the Stack (Cleanup)

**WARNING: This permanently deletes all resources.**

Empty the S3 bucket first (CloudFormation cannot delete a non-empty bucket):
```bash
aws s3 rm s3://YOUR-BUCKET-NAME --recursive
```

Then delete:
```bash
aws cloudformation delete-stack --stack-name InternshipAWSStack
```

Or in Console: CloudFormation → Stack → Delete
