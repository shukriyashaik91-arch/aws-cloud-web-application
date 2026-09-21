# EBS Backup and Restore Procedure

## What is an EBS Snapshot?

An EBS (Elastic Block Store) snapshot is a point-in-time copy of an EBS volume.
AWS stores snapshots durably in Amazon S3 (in AWS-managed storage, not your bucket).

When you create a snapshot of the EC2 root volume, you capture:
- The operating system
- Nginx web server configuration
- Deployed web application files
- All installed packages
- Log files at the time of snapshot

---

## What the Snapshot Protects Against

| Scenario | Protected? |
|---|---|
| Accidental file deletion on EC2 | ✅ Yes — restore from snapshot |
| OS corruption | ✅ Yes — create new volume from snapshot |
| EC2 instance termination | ✅ Yes — attach snapshot volume to new instance |
| Ransomware/data encryption | ✅ Yes — if snapshot was taken before infection |
| AWS hardware failure | ✅ Yes — snapshot is stored in S3 (durable) |
| S3 bucket deletion | ❌ No — snapshots do not back up S3 |
| Database data | ❌ No — this project uses no database |

---

## Step-by-Step: Create an EBS Snapshot

### Method 1 — AWS Console

1. AWS Console → EC2 → Instances
2. Click on your instance → **Storage** tab
3. Click on the Volume ID (looks like `vol-0abc123def456789`)
4. This takes you to EC2 → Volumes
5. Select the volume → **Actions** → **Create Snapshot**
6. Fill in:
   - Description: `InternshipRootSnapshot`
   - Tags: Key=`Project`, Value=`InternshipAWS`
   - Tags: Key=`Env`, Value=`Demo`
7. Click **Create Snapshot**
8. EC2 → Snapshots → View progress
9. Status changes: **Pending** → **Completed** (2–5 minutes for 8 GB)

### Method 2 — AWS CLI

```bash
# Step 1: Get your EC2 instance ID
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
echo "Instance ID: $INSTANCE_ID"

# Step 2: Get the root volume ID attached to the instance
VOLUME_ID=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query "Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId" \
  --output text)
echo "Volume ID: $VOLUME_ID"

# Step 3: Create the snapshot
SNAPSHOT_ID=$(aws ec2 create-snapshot \
  --volume-id "$VOLUME_ID" \
  --description "InternshipRootSnapshot" \
  --tag-specifications "ResourceType=snapshot,Tags=[{Key=Project,Value=InternshipAWS},{Key=Env,Value=Demo},{Key=Name,Value=InternshipRootSnapshot}]" \
  --query "SnapshotId" \
  --output text)
echo "Snapshot created: $SNAPSHOT_ID"

# Step 4: Wait for snapshot to complete
echo "Waiting for snapshot to complete..."
aws ec2 wait snapshot-completed --snapshot-ids "$SNAPSHOT_ID"
echo "Snapshot COMPLETED: $SNAPSHOT_ID"
```

---

## Step-by-Step: Restore from Snapshot

This is a documented restore procedure. The following steps describe how to
recover the instance from the snapshot. This procedure has not been run as
a live restoration — it is a documented recovery plan.

Create a new volume from the snapshot and attach it to the EC2 instance
(or a new instance) to recover data.

### Step 1 — Find the Snapshot ID

```bash
aws ec2 describe-snapshots \
  --filters "Name=tag:Project,Values=InternshipAWS" \
  --query "Snapshots[*].{ID:SnapshotId,Desc:Description,State:State,Date:StartTime}" \
  --output table
```

### Step 2 — Create a New Volume from the Snapshot

```bash
# Get your availability zone (must match EC2 instance AZ)
AZ=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query "Reservations[0].Instances[0].Placement.AvailabilityZone" \
  --output text)

# Create new volume from snapshot
NEW_VOLUME_ID=$(aws ec2 create-volume \
  --snapshot-id "$SNAPSHOT_ID" \
  --availability-zone "$AZ" \
  --volume-type gp3 \
  --tag-specifications "ResourceType=volume,Tags=[{Key=Project,Value=InternshipAWS},{Key=Name,Value=InternshipRestoredVolume}]" \
  --query "VolumeId" \
  --output text)
echo "New volume created: $NEW_VOLUME_ID"

# Wait for the volume to become available
aws ec2 wait volume-available --volume-ids "$NEW_VOLUME_ID"
echo "Volume is ready."
```

### Step 3 — Attach the Restored Volume

> ⚠️ The EC2 instance must be STOPPED before replacing the root volume.

```bash
# Stop the instance
aws ec2 stop-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID"
echo "Instance stopped."

# Detach the current root volume (if replacing the root)
aws ec2 detach-volume --volume-id "$VOLUME_ID"
aws ec2 wait volume-available --volume-ids "$VOLUME_ID"
echo "Old volume detached."

# Attach the restored volume as root device
aws ec2 attach-volume \
  --instance-id "$INSTANCE_ID" \
  --volume-id "$NEW_VOLUME_ID" \
  --device "/dev/sda1"
echo "Restored volume attached."

# Start the instance
aws ec2 start-instances --instance-ids "$INSTANCE_ID"
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"
echo "Instance started with restored volume."
```

### Step 4 — Verify Recovery

```bash
# Get new public IP (may change after stop/start unless using Elastic IP)
NEW_IP=$(aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text)
echo "New public IP: $NEW_IP"

# Test the website
curl -I "http://$NEW_IP"
curl "http://$NEW_IP/health"
```

---

## Cost Warning

| Item | Cost |
|---|---|
| EBS Snapshot (8 GB) | $0.05/GB/month = **$0.40/month** |
| Free Tier includes | **NO snapshot storage** |
| Action required | **Delete snapshot after demo** |

### Delete the Snapshot (after demonstration)

```bash
aws ec2 delete-snapshot --snapshot-id "$SNAPSHOT_ID"
echo "Snapshot deleted — no further charges."
```

Or in Console: EC2 → Snapshots → Select → Actions → Delete Snapshot

---

## Summary

| Action | Command/Location |
|---|---|
| Find volume ID | EC2 → Instances → Storage tab |
| Create snapshot | `aws ec2 create-snapshot --volume-id vol-xxx` |
| Create volume from snapshot | `aws ec2 create-volume --snapshot-id snap-xxx` |
| Attach volume | `aws ec2 attach-volume --device /dev/sda1` |
| Delete snapshot | `aws ec2 delete-snapshot --snapshot-id snap-xxx` |
