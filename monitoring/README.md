# Monitoring Configuration Guide

## Overview

CloudWatch monitors the EC2 instance and alerts via SNS email when
thresholds are exceeded. This file documents the complete monitoring setup.

---

## SNS Topic: InternshipAWSAlerts

### Create via Console
1. SNS → Topics → Create topic
2. Type: **Standard**
3. Name: `InternshipAWSAlerts`
4. Display name: `InternshipAWS CloudWatch Alerts`
5. Create topic

### Subscribe Your Email
1. SNS → Topics → InternshipAWSAlerts → Create subscription
2. Protocol: **Email**
3. Endpoint: your@email.com
4. Create subscription
5. **CHECK YOUR EMAIL** — click "Confirm subscription" in the AWS email
6. Status changes from **PendingConfirmation** → **Confirmed**

> ⚠️ Alarms will NOT send email until the subscription is confirmed.

### Get the SNS Topic ARN
```bash
aws sns list-topics
# or
aws sns list-topics --query "Topics[?contains(TopicArn, 'InternshipAWSAlerts')].TopicArn" --output text
```

---

## CloudWatch Alarms

### Alarm 1: CPU Utilisation

| Property | Value |
|---|---|
| Alarm Name | InternshipAWS-CPUUtilizationAlarm |
| Namespace | AWS/EC2 |
| Metric | CPUUtilization |
| Statistic | Average |
| Threshold | > 70% |
| Period | 300 seconds (5 minutes) |
| Evaluation Periods | 1 |
| Treat Missing Data | notBreaching |
| Action | Publish to InternshipAWSAlerts |

**Create via CLI (replace INSTANCE-ID and SNS-ARN):**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "InternshipAWS-CPUUtilizationAlarm" \
  --alarm-description "CPU > 70% for 5 minutes" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --dimensions Name=InstanceId,Value=YOUR-INSTANCE-ID \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 70 \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions YOUR-SNS-TOPIC-ARN \
  --ok-actions YOUR-SNS-TOPIC-ARN
```

### Alarm 2: Status Check Failed

| Property | Value |
|---|---|
| Alarm Name | InternshipAWS-StatusCheckAlarm |
| Namespace | AWS/EC2 |
| Metric | StatusCheckFailed |
| Statistic | Maximum |
| Threshold | >= 1 |
| Period | 300 seconds |
| Evaluation Periods | 1 |
| Treat Missing Data | notBreaching |
| Action | Publish to InternshipAWSAlerts |

**Create via CLI:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "InternshipAWS-StatusCheckAlarm" \
  --alarm-description "EC2 status check failed" \
  --metric-name StatusCheckFailed \
  --namespace AWS/EC2 \
  --statistic Maximum \
  --dimensions Name=InstanceId,Value=YOUR-INSTANCE-ID \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions YOUR-SNS-TOPIC-ARN \
  --ok-actions YOUR-SNS-TOPIC-ARN
```

---

## Testing the Alarms Safely

### Test SNS Notification (safest method)
Publish a test message directly to the SNS topic:
```bash
aws sns publish \
  --topic-arn YOUR-SNS-TOPIC-ARN \
  --subject "InternshipAWS Test Notification" \
  --message "This is a test notification from the InternshipAWS monitoring system. Alarms are configured correctly."
```
Check your email — the notification should arrive within 1 minute.

### Verify Alarm State
```bash
# List all alarms and their state
aws cloudwatch describe-alarms \
  --alarm-names \
    "InternshipAWS-CPUUtilizationAlarm" \
    "InternshipAWS-StatusCheckAlarm" \
  --query "MetricAlarms[*].{Name:AlarmName,State:StateValue,Reason:StateReason}"
```
Expected output when everything is normal:
- StateValue: `OK`

### Set Alarm to ALARM State for Demo (then reset it)
```bash
# Manually trigger the CPU alarm for demo purposes
aws cloudwatch set-alarm-state \
  --alarm-name "InternshipAWS-CPUUtilizationAlarm" \
  --state-value ALARM \
  --state-reason "Manual demo trigger for internship presentation"

# Reset back to OK after demo
aws cloudwatch set-alarm-state \
  --alarm-name "InternshipAWS-CPUUtilizationAlarm" \
  --state-value OK \
  --state-reason "Demo complete - manually reset"
```

> ⚠️ Do NOT run stress tests or artificial CPU load on a Free Tier instance.
> The `set-alarm-state` command above safely demonstrates the alarm → email flow
> without actually stressing the instance.

---

## View Metrics in Console

1. CloudWatch → Metrics → All metrics → AWS/EC2
2. Select InstanceId → Your instance
3. Select CPUUtilization
4. View graph over last 3 hours

---

## Cost Safety

| Resource | Free Tier |
|---|---|
| CloudWatch alarms | 10 alarm-metrics/month FREE |
| This project uses | **2 alarms** — well within free tier |
| SNS publishes | 1 million/month FREE |
| SNS email deliveries | 1,000/month FREE |
| CloudWatch Metrics (EC2) | EC2 basic metrics are FREE |

> Note: CloudWatch Logs (if used) can incur charges.
> This project does NOT enable CloudWatch Logs by default
> to avoid unexpected charges.
