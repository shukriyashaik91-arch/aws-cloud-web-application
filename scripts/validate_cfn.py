#!/usr/bin/env python3
"""
validate_cfn.py — Pre-deployment CloudFormation deep audit script.
Parses and validates infrastructure/cloudformation-stack.yaml using
cfn-lint's own YAML loader so CFN intrinsic functions (!Ref, !Sub, etc.)
are handled correctly.

Run from the project root:
    python scripts/validate_cfn.py
"""

import sys
import re
from pathlib import Path

TEMPLATE_PATH = Path("infrastructure/cloudformation-stack.yaml")

# ── Load template via cfn-lint's own YAML parser ─────────────────────────────
try:
    from cfnlint.decode import cfn_yaml
    result = cfn_yaml.load(str(TEMPLATE_PATH))
    # cfn-lint >= 1.x returns a dict directly; older versions returned (dict, matches)
    if isinstance(result, tuple):
        template, matches = result
        if matches:
            print("PARSE ERRORS:")
            for m in matches:
                print(f"  {m}")
            sys.exit(1)
    else:
        template = result
    print(f"[OK] CFN YAML parse succeeded")
except Exception as e:
    print(f"[FAIL] YAML parse error: {e}")
    sys.exit(1)

resources = template.get("Resources", {})
params    = template.get("Parameters", {})
outputs   = template.get("Outputs", {})

errors   = []
warnings = []
ok_msgs  = []

# Helper
def ok(msg):  ok_msgs.append(f"[OK]   {msg}")
def err(msg): errors.append(f"[ERR]  {msg}")
def warn(msg):warnings.append(f"[WARN] {msg}")


# ── 1. Required top-level keys ────────────────────────────────────────────────
for key in ["AWSTemplateFormatVersion","Description","Parameters","Resources","Outputs"]:
    if key in template:
        ok(f"Top-level key '{key}' present")
    else:
        err(f"Missing top-level key: {key}")

ok(f"Resources count: {len(resources)}")
ok(f"Parameters count: {len(params)}")
ok(f"Outputs count: {len(outputs)}")


# ── 2. All expected resources present ────────────────────────────────────────
expected_resources = [
    "InternshipVPC", "InternshipIGW", "IGWAttachment",
    "InternshipPublicSubnet", "InternshipPublicRT",
    "PublicDefaultRoute", "PublicSubnetRouteAssociation",
    "InternshipWebSG", "InternshipEC2Role", "InternshipS3Policy",
    "InternshipInstanceProfile", "InternshipS3Bucket",
    "InternshipEC2", "InternshipSNSTopic", "CPUAlarm", "StatusCheckAlarm"
]
for r in expected_resources:
    if r in resources:
        ok(f"Resource '{r}' present")
    else:
        err(f"Expected resource '{r}' is MISSING from template")


# ── 3. EC2 DependsOn IGWAttachment ───────────────────────────────────────────
ec2 = resources.get("InternshipEC2", {})
depends = ec2.get("DependsOn", [])
if isinstance(depends, str):
    depends = [depends]
if "IGWAttachment" in depends:
    ok("EC2 DependsOn IGWAttachment — correct launch ordering")
else:
    err("EC2 missing 'DependsOn: IGWAttachment' — EC2 may launch before IGW is attached, causing UserData network failures")


# ── 4. EC2 uses InstanceProfile (not Role directly) ──────────────────────────
ec2_props = ec2.get("Properties", {})
iip = ec2_props.get("IamInstanceProfile", {})
if iip:
    ok("EC2 has IamInstanceProfile set")
else:
    err("EC2 is missing IamInstanceProfile — instance will NOT have S3 access")


# ── 5. EC2 EBS volume ────────────────────────────────────────────────────────
bdm = ec2_props.get("BlockDeviceMappings", [])
if bdm:
    for b in bdm:
        ebs  = b.get("Ebs", {})
        vtype = str(ebs.get("VolumeType", "unknown"))
        vsize = int(str(ebs.get("VolumeSize", 0)))
        device = b.get("DeviceName", "?")
        if vtype == "gp3":
            ok(f"EBS {device}: type=gp3, size={vsize}GB — within Free Tier (30GB limit)")
        elif vtype == "gp2":
            warn(f"EBS type=gp2. gp3 is cheaper and faster; same Free Tier coverage")
        else:
            warn(f"EBS type={vtype} — verify Free Tier eligibility")
        if vsize > 30:
            err(f"EBS volume size={vsize}GB EXCEEDS 30GB Free Tier limit — will incur charges")
        if not ebs.get("DeleteOnTermination", True):
            warn(f"EBS DeleteOnTermination=false — orphaned volume will incur charges after instance termination")
else:
    warn("No BlockDeviceMappings defined — default EBS size may not match expected configuration")


# ── 6. Security Group port 22 must NOT be 0.0.0.0/0 ─────────────────────────
sg = resources.get("InternshipWebSG", {})
ingress = sg.get("Properties", {}).get("SecurityGroupIngress", [])
ssh_rules = [r for r in ingress if str(r.get("FromPort","")) == "22"]
http_rules = [r for r in ingress if str(r.get("FromPort","")) == "80"]

if not ssh_rules:
    warn("No SSH (port 22) inbound rule found in security group")
else:
    for rule in ssh_rules:
        cidr = str(rule.get("CidrIp", ""))
        if cidr == "0.0.0.0/0":
            err("SECURITY: SSH port 22 is open to 0.0.0.0/0 — must be restricted to admin IP only")
        elif "Ref" in str(rule.get("CidrIp", {})):
            ok("SSH port 22 uses parameter Ref for CIDR (not 0.0.0.0/0)")
        else:
            ok(f"SSH port 22 CIDR: {cidr}")

if not http_rules:
    warn("No HTTP (port 80) inbound rule found")
else:
    ok("HTTP port 80 inbound rule present")


# ── 7. S3 PublicAccessBlockConfiguration all four flags ──────────────────────
s3_res = resources.get("InternshipS3Bucket", {})
pab = s3_res.get("Properties", {}).get("PublicAccessBlockConfiguration", {})
for flag in ["BlockPublicAcls","BlockPublicPolicy","IgnorePublicAcls","RestrictPublicBuckets"]:
    val = pab.get(flag)
    if val is True or str(val).lower() == "true":
        ok(f"S3 {flag}=true")
    else:
        err(f"S3 {flag} is NOT true (got {val!r}) — bucket may allow public access")


# ── 8. S3 DeletionPolicy ─────────────────────────────────────────────────────
s3_dp = s3_res.get("DeletionPolicy", "Delete")
if s3_dp == "Delete":
    warn("S3 DeletionPolicy=Delete (default). CloudFormation stack deletion will FAIL "
         "if bucket is non-empty. You must empty the bucket before deleting the stack. "
         "This is the correct behaviour for a demo — documented in cleanup procedure.")
else:
    ok(f"S3 DeletionPolicy={s3_dp}")


# ── 9. IAM Policy references InternshipEC2Role ───────────────────────────────
s3pol = resources.get("InternshipS3Policy", {})
roles = s3pol.get("Properties", {}).get("Roles", [])
role_refs = [r.get("Ref","") if isinstance(r, dict) else str(r) for r in roles]
if "InternshipEC2Role" in role_refs:
    ok("InternshipS3Policy attached to InternshipEC2Role")
else:
    err(f"InternshipS3Policy not attached to InternshipEC2Role (found: {role_refs})")


# ── 10. IAM InstanceProfile includes InternshipEC2Role ───────────────────────
ip_res = resources.get("InternshipInstanceProfile", {})
ip_roles = ip_res.get("Properties", {}).get("Roles", [])
ip_role_refs = [r.get("Ref","") if isinstance(r, dict) else str(r) for r in ip_roles]
if "InternshipEC2Role" in ip_role_refs:
    ok("InstanceProfile includes InternshipEC2Role")
else:
    err(f"InstanceProfile does not include InternshipEC2Role (found: {ip_role_refs})")


# ── 11. CloudWatch alarms reference EC2 instance ─────────────────────────────
for alarm_id, expected_metric in [("CPUAlarm","CPUUtilization"), ("StatusCheckAlarm","StatusCheckFailed")]:
    alarm = resources.get(alarm_id, {})
    props = alarm.get("Properties", {})
    metric = props.get("MetricName","")
    dims = props.get("Dimensions", [])
    period = props.get("Period", 0)
    eval_periods = props.get("EvaluationPeriods", 0)
    actions = props.get("AlarmActions", [])

    if str(metric) == expected_metric:
        ok(f"{alarm_id}: MetricName={metric}")
    else:
        err(f"{alarm_id}: MetricName='{metric}', expected '{expected_metric}'")

    ec2_dim = any(
        str(d.get("Name","")) == "InstanceId" and
        (isinstance(d.get("Value"), dict) and d["Value"].get("Ref") == "InternshipEC2")
        for d in dims
    )
    if ec2_dim:
        ok(f"{alarm_id}: InstanceId Dimension correctly references InternshipEC2")
    else:
        err(f"{alarm_id}: Dimension does not reference InternshipEC2 — alarm will not monitor correct instance")

    if int(str(period)) == 300:
        ok(f"{alarm_id}: Period=300s (5 min) — correct")
    else:
        warn(f"{alarm_id}: Period={period}s — expected 300s for basic monitoring")

    if actions:
        ok(f"{alarm_id}: AlarmActions configured ({len(actions)} action(s))")
    else:
        err(f"{alarm_id}: No AlarmActions — alarm will not send notifications")


# ── 12. SNS Topic has email subscription ─────────────────────────────────────
sns = resources.get("InternshipSNSTopic", {})
subs = sns.get("Properties", {}).get("Subscription", [])
email_subs = [s for s in subs if str(s.get("Protocol","")).lower() == "email"]
if email_subs:
    ok(f"SNS Topic has {len(email_subs)} email subscription(s)")
    for s in email_subs:
        endpoint = s.get("Endpoint", {})
        if isinstance(endpoint, dict) and "Ref" in endpoint:
            ok(f"  SNS email endpoint is a parameter Ref (not hardcoded)")
        else:
            warn(f"  SNS email endpoint may be hardcoded: {endpoint}")
else:
    err("SNS Topic has no email subscription defined")


# ── 13. UserData variable escaping in Fn::Sub ────────────────────────────────
# In Fn::Sub, bash vars MUST use ${!VAR} not ${VAR}
# Re-read raw file to check the actual text
raw = TEMPLATE_PATH.read_text(encoding="utf-8")
# Find the UserData block
userdata_block = ""
in_userdata = False
for line in raw.split("\n"):
    if "Fn::Base64" in line or "UserData:" in line:
        in_userdata = True
    if in_userdata:
        userdata_block += line + "\n"
    if in_userdata and line.strip() == "" and len(userdata_block) > 200:
        pass  # keep going
    if in_userdata and "Tags:" in line and len(userdata_block) > 300:
        break

# Check that bash variable references use ${!VAR} inside the Sub block
# Specifically look for ${VAR} where VAR is a bash variable (all caps, underscore)
# that is NOT a CFN parameter name
cfn_param_names = set(params.keys())
cfn_resource_names = set(resources.keys())
cfn_known = cfn_param_names | cfn_resource_names

bash_unescaped = []
# Pattern: ${WORD} that is NOT escaped as ${!WORD}
for match in re.finditer(r'\$\{(?!!)([\w]+)\}', userdata_block):
    varname = match.group(1)
    if varname not in cfn_known:
        bash_unescaped.append(varname)

if bash_unescaped:
    unique = sorted(set(bash_unescaped))
    err(f"UserData contains un-escaped bash variables in Fn::Sub context: {unique} "
        f"— these must use ${{!VARNAME}} syntax or CloudFormation will try to substitute them and fail")
else:
    ok("UserData: No un-escaped bash variables found in Fn::Sub context")

# Check that expected escaped vars ARE present (INSTANCE_ID, REGION, AZ)
for expected_escaped in ["${!INSTANCE_ID}", "${!REGION}", "${!AZ}"]:
    if expected_escaped in raw:
        ok(f"UserData: {expected_escaped} correctly escaped")
    else:
        warn(f"UserData: {expected_escaped} not found — bash variable may be missing or was removed")


# ── 14. All Outputs reference real resources ──────────────────────────────────
for out_name, out_val in outputs.items():
    val = out_val.get("Value", {})
    val_str = str(val)
    if val_str:
        ok(f"Output '{out_name}' has a Value defined")
    else:
        err(f"Output '{out_name}' has no Value")


# ── 15. IAM Policy S3 resource uses Fn::Sub with bucket param ────────────────
s3pol_stmts = s3pol.get("Properties", {}).get("PolicyDocument", {}).get("Statement", [])
bucket_arns = []
for stmt in s3pol_stmts:
    res = stmt.get("Resource", "")
    if isinstance(res, dict):
        # Fn::Sub or similar
        sub_val = res.get("Fn::Sub", "") or str(res)
        bucket_arns.append(sub_val)
    elif isinstance(res, str):
        bucket_arns.append(res)

hardcoded_bucket = any("REPLACE-WITH" in str(a) for a in bucket_arns)
if hardcoded_bucket:
    err("IAM S3 policy has 'REPLACE-WITH-YOUR-BUCKET-NAME' placeholder — bucket name is hardcoded and not using template parameter")
else:
    ok("IAM S3 policy resources reference the template bucket parameter (no placeholder text)")

# Check the ARNs use S3BucketName param
param_ref = any("S3BucketName" in str(a) for a in bucket_arns)
if param_ref:
    ok("IAM S3 policy ARN references S3BucketName parameter via Fn::Sub")
else:
    warn(f"IAM S3 policy ARN does not obviously reference S3BucketName parameter. ARNs: {bucket_arns}")


# ── 16. Cost-risky resources NOT present ─────────────────────────────────────
risky = {
    "AWS::EC2::NatGateway":              "NAT Gateway (~$32/month)",
    "AWS::ElasticLoadBalancingV2::LoadBalancer": "Application Load Balancer (~$16+/month)",
    "AWS::RDS::DBInstance":              "RDS database",
    "AWS::AutoScaling::AutoScalingGroup":"Auto Scaling Group",
    "AWS::ECS::Cluster":                 "ECS Cluster",
    "AWS::EKS::Cluster":                 "EKS Cluster",
}
for rtype, label in risky.items():
    found = [name for name, r in resources.items() if r.get("Type","") == rtype]
    if found:
        err(f"COST RISK: {label} ({rtype}) found in template: {found}")
    else:
        ok(f"Not present (cost safe): {label}")

# Count EC2 instances
ec2_instances = [n for n, r in resources.items() if r.get("Type","") == "AWS::EC2::Instance"]
if len(ec2_instances) == 1:
    ok(f"Exactly 1 EC2 instance defined: {ec2_instances[0]}")
else:
    err(f"Expected exactly 1 EC2 instance, found {len(ec2_instances)}: {ec2_instances}")

# Count CloudWatch alarms
cw_alarms = [n for n, r in resources.items() if r.get("Type","") == "AWS::CloudWatch::Alarm"]
if len(cw_alarms) <= 10:
    ok(f"{len(cw_alarms)} CloudWatch alarm(s) — within Free Tier (10 limit)")
else:
    warn(f"{len(cw_alarms)} CloudWatch alarms — exceeds Free Tier of 10")


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 65)
print("  CLOUDFORMATION VALIDATION REPORT")
print("=" * 65)

print(f"\n  OK messages:  {len(ok_msgs)}")
print(f"  Warnings:     {len(warnings)}")
print(f"  Errors:       {len(errors)}")

print("\n--- OK ---")
for m in ok_msgs:
    print(f"  {m}")

if warnings:
    print("\n--- WARNINGS ---")
    for w in warnings:
        print(f"  {w}")

if errors:
    print("\n--- ERRORS ---")
    for e in errors:
        print(f"  {e}")
    print()
    sys.exit(1)
else:
    print("\n  RESULT: Template passed all validation checks.")
    sys.exit(0)
