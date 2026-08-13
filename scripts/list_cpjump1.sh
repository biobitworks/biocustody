#!/usr/bin/env bash
set -euo pipefail
BUCKET="s3://cellpainting-gallery/cpg0000-jump-pilot"
echo "Listing top level:"
aws s3 ls --no-sign-request "${BUCKET}/"
echo
echo "Processed well-level data are documented under:"
echo "${BUCKET}/source_4/workspace/backend/<BATCH>/"
echo
echo "Do NOT recursively sync the full dataset. List a batch, choose a plate, then copy only the files needed."
