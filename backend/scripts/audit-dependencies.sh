#!/usr/bin/env sh
set -eu

mkdir -p /reports
pip freeze --all > /reports/python-dependencies.txt

pip_audit_status=0
safety_status=0
pip-audit --requirement /app/requirements.txt --format json --output /reports/pip-audit.json || pip_audit_status=$?
safety check --file /app/requirements.txt --full-report --json > /reports/safety.json || safety_status=$?

cat > /reports/audit-summary.txt <<EOF
pip-audit exit status: ${pip_audit_status}
safety exit status: ${safety_status}
EOF

# A non-zero exit is deliberate: the audit profile must fail CI when either
# scanner reports a vulnerability or cannot complete.
if [ "$pip_audit_status" -ne 0 ]; then exit "$pip_audit_status"; fi
exit "$safety_status"
