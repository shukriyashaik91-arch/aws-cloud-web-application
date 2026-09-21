# IAM Configuration Guide

## Overview

This project uses the following IAM structure.
All resources follow the principle of **least privilege**.

---

## Resources to Create

### 1. IAM Groups

#### Group: InternDevelopers
- **Purpose:** Developers working on the project
- **Suggested policies:** ReadOnlyAccess (or a custom policy for dev access)
- **Console:** IAM → Groups → Create Group → Name: `InternDevelopers`

#### Group: CloudOperators
- **Purpose:** Operations team managing the infrastructure
- **Suggested policies:** PowerUserAccess (restricted as needed)
- **Console:** IAM → Groups → Create Group → Name: `CloudOperators`

---

### 2. IAM User: aws-project-user

- **Purpose:** Day-to-day project administration
- **Group:** Add to both `InternDevelopers` and `CloudOperators`
- **MFA:** Enable MFA on this user

**Create via Console:**
1. IAM → Users → Create User
2. Name: `aws-project-user`
3. Enable console access
4. Add to groups: InternDevelopers, CloudOperators
5. Attach permissions as needed

**Create via CLI:**
```bash
# Create user
aws iam create-user --user-name aws-project-user

# Add to groups
aws iam add-user-to-group --user-name aws-project-user --group-name InternDevelopers
aws iam add-user-to-group --user-name aws-project-user --group-name CloudOperators

# Create access key (for CLI use — store securely, NEVER commit)
aws iam create-access-key --user-name aws-project-user
```

---

### 3. IAM Role: InternshipEC2S3Role

This role is attached to the EC2 instance.
It allows the EC2 instance to access S3 without any hardcoded credentials.

**Trust Policy** (EC2 can assume this role):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "ec2.amazonaws.com" },
    "Action": "sts:AssumeRole"
  }]
}
```

**Permission Policy** (see policies/ec2-s3-policy.json):
- `s3:ListBucket` on the project bucket ARN
- `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on bucket objects

**Replace `REPLACE-WITH-YOUR-BUCKET-NAME`** in the policy file before applying.

**Create via CLI:**
```bash
# Create role with EC2 trust policy
aws iam create-role \
  --role-name InternshipEC2S3Role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

# Create the S3 access policy (after updating the bucket name in the JSON)
aws iam create-policy \
  --policy-name InternshipS3BucketPolicy \
  --policy-document file://iam/policies/ec2-s3-policy.json

# Attach policy to role
aws iam attach-role-policy \
  --role-name InternshipEC2S3Role \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/InternshipS3BucketPolicy

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name InternshipInstanceProfile

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name InternshipInstanceProfile \
  --role-name InternshipEC2S3Role
```

**NOTE:** If using the CloudFormation stack (cloudformation-stack.yaml),
all IAM resources above are created automatically.

---

## Security Rules Applied

| Rule | Implementation |
|---|---|
| Least privilege | EC2 role only has access to the project bucket |
| No root credentials | Root is only used for billing — use aws-project-user for everything else |
| No hardcoded keys | EC2 uses Instance Role, not access key ID/secret |
| MFA recommended | Enable MFA on aws-project-user and root accounts |
| Key rotation | IAM access keys should be rotated every 90 days |
| .pem file secured | In .gitignore, never committed |
| No wildcard resources | S3 policy uses specific ARNs, not `arn:aws:s3:::*` |

---

## Verifying the EC2 Role Works

SSH into the EC2 instance and test:

```bash
# This should SUCCEED (project bucket)
aws s3 ls s3://YOUR-PROJECT-BUCKET

# This should FAIL with AccessDenied (different bucket)
aws s3 ls s3://some-other-bucket
# Expected: An error occurred (AccessDenied) when calling the ListObjects operation

# Verify which role is being used
aws sts get-caller-identity
# Expected output shows the InternshipEC2S3Role ARN — NOT any user access key
```
