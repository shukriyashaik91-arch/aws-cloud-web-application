# Monitoring Documentation

## Overview

The application is monitored using Amazon CloudWatch.
Alarms send notifications via Amazon SNS to a confirmed email address.

---

## Metrics Monitored

### 1. CPUUtilization
- **Source:** AWS/EC2 namespace (collected automatically — no agent needed)
- **Frequency:** Every 5 minutes (Basic Monitoring — Free Tier)
- **Alarm threshold:** > 70% for 5 consecutive minutes
- **Why this matters:** High CPU could mean the application is overloaded,
  a process is stuck, or the instance type is insufficient.

### 2. StatusCheckFailed
- **Source:** AWS/EC2 namespace (collected automatically)
- **Frequency:** Every minute
- **Alarm threshold:** >= 1 failure
- **Why this matters:** Combines instance and system status checks.
  A failure indicates the VM is unreachable or the hardware is degraded.

---

## Alarm States

CloudWatch alarms have three states:

| State | Meaning |
|---|---|
| OK | Metric is within threshold — everything normal |
| ALARM | Metric crossed the threshold — action taken (SNS email sent) |
| INSUFFICIENT_DATA | Not enough data yet — usually seen after alarm creation |

---

## SNS Topic: InternshipAWSAlerts

The topic receives ALARM state change notifications from both CloudWatch alarms
and delivers them to your confirmed email within ~1 minute.

**Email format you receive:**
```
Subject: ALARM: "InternshipAWS-CPUUtilizationAlarm" in US East (N. Virginia)

You are receiving this email because your Amazon CloudWatch Alarm
"InternshipAWS-CPUUtilizationAlarm" in the US East (N. Virginia)
region has entered the ALARM state...

Alarm details:
  Name:        InternshipAWS-CPUUtilizationAlarm
  State change: OK -> ALARM
  Reason:      Threshold Crossed: 1 datapoint [72.5] was greater than
               the threshold (70.0).
  Timestamp:   Wednesday 26 August, 2026 14:32:00 UTC
```

---

## Viewing Metrics in the Console

1. CloudWatch → Metrics → All metrics
2. AWS namespaces → EC2 → Per-Instance Metrics
3. Select your Instance ID
4. Select CPUUtilization or StatusCheckFailed
5. Click "Add to graph"
6. Adjust time range to "Last 3 hours"

---

## Verifying Alarms are Configured

```bash
# List alarm details
aws cloudwatch describe-alarms \
  --alarm-name-prefix "InternshipAWS" \
  --query "MetricAlarms[*].{
    Name:AlarmName,
    State:StateValue,
    Metric:MetricName,
    Threshold:Threshold,
    Operator:ComparisonOperator
  }" \
  --output table
```

---

## Testing Alarm → Email Flow (Safe Method)

Use the `set-alarm-state` API to manually trigger the alarm state.
This is the safe demo method — no CPU stress needed.

```bash
# Get your SNS topic ARN
SNS_ARN=$(aws sns list-topics \
  --query "Topics[?contains(TopicArn,'InternshipAWSAlerts')].TopicArn" \
  --output text)

# Test 1: Direct SNS publish (fastest test)
aws sns publish \
  --topic-arn "$SNS_ARN" \
  --subject "InternshipAWS Test — Monitoring Working" \
  --message "Monitoring system tested successfully on $(date -u)"

# Test 2: Trigger actual alarm state change (shows full alarm flow)
aws cloudwatch set-alarm-state \
  --alarm-name "InternshipAWS-CPUUtilizationAlarm" \
  --state-value ALARM \
  --state-reason "Demo test — manual trigger for internship presentation"

# Check email — you should receive the ALARM notification

# Reset back to OK after 2 minutes
aws cloudwatch set-alarm-state \
  --alarm-name "InternshipAWS-CPUUtilizationAlarm" \
  --state-value OK \
  --state-reason "Demo complete — manually reset to OK"
```

---

## Cost Summary

| Resource | Free Tier | This Project |
|---|---|---|
| EC2 Basic Metrics | Always free | Both metrics (CPU, Status) |
| CloudWatch Alarms | 10 alarm-metrics/month free | 2 alarms used |
| SNS Standard | 1M publishes/month free | <10 for demo |
| SNS Email | 1,000/month free | <10 for demo |
| CloudWatch Logs | 5 GB/month free (first 12 months) | Not used |

**This monitoring setup costs $0.00.**
