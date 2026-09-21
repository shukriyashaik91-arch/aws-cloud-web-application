# Security Documentation

## Security Principles Applied

This project follows the AWS Well-Architected Framework security pillar.

---

## 1. Identity and Access Management

### IAM Users and Groups
| Resource | Purpose | Security Level |
|---|---|---|
| Root account | Billing only — never used for dev | Protected with MFA |
| aws-project-user | Daily administration | MFA recommended |
| InternDevelopers group | Grouped developer permissions | Least privilege |
| CloudOperators group | Grouped operations permissions | Least privilege |

### IAM Role: InternshipEC2S3Role
The most important security decision in this project.

**Why a role, not an access key?**
- Access keys are static — if stolen, they work until manually rotated
- IAM roles provide temporary credentials — AWS rotates them every hour automatically
- No key to accidentally commit to git
- No key to store in environment variables or config files

**The principle of least privilege:**
```json
{
  "Effect": "Allow",
  "Action": ["s3:ListBucket"],
  "Resource": "arn:aws:s3:::SPECIFIC-PROJECT-BUCKET"
}
```
The policy specifies the exact bucket ARN — not `arn:aws:s3:::*`.
This means the EC2 instance cannot access any other S3 bucket.

---

## 2. Network Security

### Security Group Rules
| Direction | Protocol | Port | Source/Destination | Reason |
|---|---|---|---|---|
| Inbound | TCP | 22 | Admin IP /32 | SSH for administration only |
| Inbound | TCP | 80 | 0.0.0.0/0 | Public website access |
| Outbound | All | All | 0.0.0.0/0 | Software updates, S3 access |
| All other inbound | — | — | BLOCKED | No unnecessary exposure |

**Why not SSH from 0.0.0.0/0?**
Port 22 open to the world attracts constant brute-force attacks.
Restricting to your IP makes attacks practically impossible.

### VPC Isolation
The VPC provides a private network boundary. Resources inside the VPC
cannot be accessed from outside unless explicitly allowed by security groups.
No private subnet was created because a NAT Gateway would be needed —
which costs ~$32/month.

---

## 3. Data Security

### S3 Bucket Security
| Setting | Value | Why |
|---|---|---|
| Block Public ACLs | ✅ ON | Prevents public object access via ACL |
| Block Public Policies | ✅ ON | Prevents bucket policy granting public access |
| Ignore Public ACLs | ✅ ON | Ensures existing public ACLs are ignored |
| Restrict Public Buckets | ✅ ON | Prevents any public access |
| Versioning | Off | Saves cost — demo project |

The bucket contains no sensitive personal data.
It stores HTML, CSS, log files, and a sample dataset — none of which
require encryption for this demonstration.

---

## 4. Credential Hygiene

| Rule | How Enforced |
|---|---|
| No .pem files in git | .gitignore blocks *.pem, *.ppk |
| No .env files in git | .gitignore blocks .env |
| No AWS keys in code | EC2 uses IAM role — no keys needed |
| No account ID in code | No AWS access keys or secret credentials are hardcoded in the application |
| No secrets in screenshots | Documentation explicitly warns about this |

### .gitignore Coverage
The .gitignore file blocks:
- `*.pem` — EC2 key pairs
- `*.ppk` — PuTTY key pairs
- `.env*` — Environment files
- `credentials` — AWS credentials files
- `secrets.*` — Any secrets file

---

## 5. Security Checks Performed

### Before Running
- [ ] SSH not open to 0.0.0.0/0
- [ ] S3 bucket public access blocked
- [ ] No access keys in source code
- [ ] .pem file secured and .gitignored
- [ ] IAM role uses specific bucket ARN (not `*`)

### After Deployment
Run these checks to verify security:

```bash
# Verify SSH is restricted (should show your IP, not 0.0.0.0/0)
aws ec2 describe-security-groups \
  --group-names InternshipAWS-WebSG \
  --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`]"

# Verify S3 is private
aws s3api get-bucket-acl --bucket YOUR-BUCKET
aws s3api get-public-access-block --bucket YOUR-BUCKET

# Verify EC2 is using IAM role (not access keys)
# Run from EC2 instance:
aws sts get-caller-identity
# Expected: shows InternshipEC2S3Role ARN, not any IAM user

# Test unauthorized S3 access is denied
aws s3 ls s3://some-other-bucket-not-yours
# Expected: AccessDenied (403)
```

---

## 6. Security Anti-Patterns Avoided

| Anti-Pattern | Why Dangerous | How Avoided |
|---|---|---|
| SSH from 0.0.0.0/0 | Brute force attacks | Restricted to admin IP |
| EC2 access keys | Key leakage risk | IAM Instance Role used |
| Public S3 bucket | Data exposure | Block public access enabled |
| Wildcard S3 policy | Over-permissive | Specific bucket ARN used |
| Root account for dev | Root has unlimited access | aws-project-user used |
| Committing .pem | Anyone with repo can SSH | .gitignore prevents commit |
| Credentials in code | Git history exposure | No credentials in code |
