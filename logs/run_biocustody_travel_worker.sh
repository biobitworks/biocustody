#!/usr/bin/env bash
cd /Users/byron/projects/inbox/biocustody-stateshift-aws-bootstrap-v0.2.0 || exit 1
set -o pipefail
echo MAGICSTUDIOBOX_TRAVEL_QUEUE_START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
.venv/bin/python scripts/magicstudiobox_repurposing_queue.py 2>&1
rc=${PIPESTATUS[0]}
echo MAGICSTUDIOBOX_TRAVEL_QUEUE_SCRIPT_RC=$rc
git add -A
git commit -m "magicstudiobox bounded repurposing sweep" || true
echo MAGICSTUDIOBOX_TRAVEL_QUEUE_EXIT_RC=$rc
echo MAGICSTUDIOBOX_TRAVEL_QUEUE_DONE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
exit $rc
