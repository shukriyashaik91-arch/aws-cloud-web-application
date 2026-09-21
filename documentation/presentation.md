# Internship Presentation & Demo Flow

## Duration: 7–10 minutes

This guide shows exactly what to say and what to click during your demo.
Practice it twice before the actual presentation.

---

## Preparation (Before the Evaluator Arrives)

- [ ] EC2 instance is running
- [ ] Website loads: http://EC2-PUBLIC-IP
- [ ] Health page works: http://EC2-PUBLIC-IP/health
- [ ] AWS Console open in browser (logged in as aws-project-user, NOT root)
- [ ] Terminal open with analyze_logs.py ready to run
- [ ] Screenshots folder ready as backup if internet is slow
- [ ] This script printed out or on a second screen

---

## Segment 1 — Introduction (60 seconds)

**What to say:**
> "I built a complete AWS cloud web application as my internship project.
> The project demonstrates eight core AWS services working together:
> VPC networking, EC2 compute, S3 storage, IAM security, CloudWatch monitoring,
> SNS alerting, EBS backup, and AWS Budgets for cost control.
> Everything is designed to run within the AWS Free Tier."

**What to show:**
- Project folder structure in VS Code or File Explorer
- README.md briefly

---

## Segment 2 — Architecture (60 seconds)

**What to say:**
> "Here's the architecture. The application runs on a single EC2 t3.micro
> instance inside a custom VPC with a public subnet.
> The Internet Gateway allows users to reach the web server over HTTP.
> The EC2 instance connects to a private S3 bucket using an IAM Instance Role —
> no hardcoded credentials anywhere.
> CloudWatch monitors the instance and sends SNS email alerts if CPU exceeds
> 70% or if a status check fails."

**What to show:**
- documentation/architecture.md (open in browser/editor)
- OR scroll to the Architecture section of the live website

---

## Segment 3 — Live Website (90 seconds)

**What to say:**
> "Let me show the live application."

**What to do:**
1. Open browser → http://EC2-PUBLIC-IP
2. Say: "This is the Student Internship Cloud Portal, hosted on EC2 using Nginx."
3. Scroll slowly through the page:
   - Hero section: "Title and project description"
   - Services section: "Cards for each AWS service"
   - Architecture section: "Visual data flow diagrams"
   - Security section: "Security decisions we made"
   - Monitoring section: "CloudWatch alarms"
   - Backup section: "EBS snapshot recovery steps"
   - Cost section: "How we stay within Free Tier"
4. Navigate to: http://EC2-PUBLIC-IP/health
5. Say: "The /health endpoint confirms the application is running.
   This could be used by a monitoring system or load balancer health check."

---

## Segment 4 — VPC and Networking (60 seconds)

**What to say:**
> "Let me show the AWS networking configuration."

**What to do:**
1. AWS Console → VPC
2. Show VPC: "Custom VPC with CIDR 10.0.0.0/16 — isolated from other AWS resources."
3. Show Subnet: "Public subnet 10.0.1.0/24 — auto-assigns public IPs."
4. Show Route Table: "Route 0.0.0.0/0 to Internet Gateway — enables internet access."
5. Show Security Group: "Port 22 restricted to my IP only. Port 80 open for the website."
6. Say: "No NAT Gateway — that would cost $32 per month. Not needed for this demo."

---

## Segment 5 — IAM and Security (60 seconds)

**What to say:**
> "Security is the most important part. Let me show the IAM configuration."

**What to do:**
1. IAM → Roles → Show InternshipAWS-EC2S3Role
2. Say: "This role is attached directly to the EC2 instance.
   Instead of storing access keys, the instance requests temporary credentials
   from AWS automatically. If someone breaks into the server,
   there are no long-lived keys to steal."
3. Click on the attached policy
4. Say: "The policy only allows access to our specific S3 bucket — not all of S3.
   s3:GetObject, s3:PutObject, and s3:ListBucket — nothing else."
5. IAM → Users → Show aws-project-user
6. Say: "I never use the root account for daily work. This IAM user handles
   all administration with limited permissions."

---

## Segment 6 — S3 Integration (60 seconds)

**What to say:**
> "The S3 bucket stores assets, logs, and the dataset."

**What to do:**
1. S3 → Show the bucket
2. Browse the folders: assets/, logs/, dataset/
3. Show the web-access-logs.csv in the dataset/ folder
4. Permissions tab: "All public access is blocked. Nothing in this bucket
   is publicly readable."
5. **On EC2 (SSH or show a screenshot):**
   ```bash
   aws sts get-caller-identity
   # Shows the IAM role — no access key
   aws s3 ls s3://YOUR-BUCKET/
   # Succeeds — authorized bucket
   ```

---

## Segment 7 — CloudWatch Monitoring (60 seconds)

**What to say:**
> "The application is continuously monitored using CloudWatch."

**What to do:**
1. CloudWatch → Alarms → Show both alarms
2. Say: "Alarm 1: If CPU exceeds 70% for 5 minutes — triggers an email alert."
3. Say: "Alarm 2: If the EC2 status check fails — triggers an email alert."
4. **Demo the alarm (optional but impressive):**
   ```bash
   aws cloudwatch set-alarm-state \
     --alarm-name "InternshipAWS-CPUUtilizationAlarm" \
     --state-value ALARM \
     --state-reason "Demo trigger for presentation"
   ```
5. Show the alarm turning red in the console
6. Say: "Within about 60 seconds, an email will arrive."
7. Show the email (prepared screenshot if live is slow)
8. Reset: `--state-value OK --state-reason "Demo complete"`

---

## Segment 8 — EBS Backup (30 seconds)

**What to say:**
> "For backup, I created an EBS snapshot of the root volume."

**What to do:**
1. EC2 → Snapshots → Show the snapshot
2. Say: "This snapshot captures the full disk state — OS, Nginx, application.
   If the server fails, I can create a new volume from this snapshot,
   attach it to a replacement EC2 instance, and recover the application
   by following the documented restore procedure."
3. Show documentation/backup-restore.md briefly

---

## Segment 9 — Log Analysis (60 seconds)

**What to say:**
> "I created a Python log analysis script to analyse web access patterns."

**What to do:**
1. Open terminal
2. Run:
   ```bash
   python scripts/analyze_logs.py
   ```
3. Walk through the output:
   - "192 total requests in the dataset"
   - "Most requested page: / — the home page"
   - "18 client errors, 3 server errors"
   - "Peak hour: 14:00 UTC"
   - "11 unique visitor IPs"
   - "92% of requests are GET"
4. Say: "This script uses only Python's standard library — no pip install needed.
   In a real environment, these logs would come from actual Nginx access logs."

---

## Segment 10 — Cost Control (30 seconds)

**What to say:**
> "Finally, cost control. This entire project runs on the AWS Free Tier."

**What to do:**
1. AWS Billing → Budgets → Show the two alerts ($1 and $3)
2. Say: "I get an email if my charges exceed $1 or $3, so I'm never surprised
   by unexpected bills."
3. Say: "I deliberately avoided NAT Gateway ($32/month), Load Balancer ($16+),
   and multiple EC2 instances. This project costs effectively $0 per month
   — with the exception of the EBS snapshot ($0.40) which I'll delete
   after this demonstration."

---

## Segment 11 — Conclusion (30 seconds)

**What to say:**
> "To summarise: I built a working cloud application that demonstrates
> VPC networking, EC2 compute, S3 storage, IAM security with least privilege,
> CloudWatch monitoring with SNS alerting, EBS snapshot backup,
> and AWS Budgets for cost control.
> The project is documented, version-controlled, and all infrastructure
> is defined as code using CloudFormation — so it can be reproduced exactly."

**Optional:**
> "I'm happy to answer any questions about any component."

---

## Backup Slides / Talking Points

If you are asked a question you're unsure about:

**Q: Why not use HTTPS?**
> "HTTPS requires a domain name and ACM certificate. This demo uses HTTP
> to keep the focus on the core AWS services. In production I would add
> an SSL certificate."

**Q: Why not use a database?**
> "RDS is not Free Tier eligible after the trial period and was not needed
> for this demonstration. The log analysis uses a CSV file stored in S3."

**Q: Can this scale?**
> "Yes — the architecture could scale by adding an Auto Scaling Group,
> Application Load Balancer, and RDS. Those were deliberately excluded
> to stay within Free Tier for this internship demo."

**Q: What is the IAM role trust policy?**
> "The trust policy allows the EC2 service (ec2.amazonaws.com) to assume
> the role. This is what enables the instance to call the IAM API and
> get temporary credentials automatically."

**Q: How would you monitor 5xx errors?**
> "I would add a CloudWatch Logs agent to ship Nginx access logs to
> CloudWatch Logs, then create a metric filter for status codes ≥ 500,
> and add a fourth alarm on that custom metric."
