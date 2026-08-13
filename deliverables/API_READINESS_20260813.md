# API Readiness - magicPRObox

Checked on `magicPRObox.local` at 2026-08-13.

## Ready

- Kaggle CLI works from `.venv/bin/kaggle`.
- Kaggle account is `biobitworks`.
- Kaggle config exists at `~/.kaggle/kaggle.json` with mode `0600`.
- Kaggle kernel `biobitworks/bio-delta-g-cpjump1-sweep` is visible and `COMPLETE`.
- CPJUMP1 public Cell Painting Gallery S3 metadata is readable.
- Kaggle outputs are pulled locally under `runs/kaggle_output/`.
- Offline bundle exists at `deliverables/bio-delta-g-magicprobox-offline-bundle-20260813.zip`.
- Muni login works for `byron@biobitworks.com`.
- Muni balance checked live on 2026-08-13: `12.464793` credits. Credits are not exhausted.
- Muni shows `onepot`.
- Muni shows Rowan tools, including `rowan_descriptors`.
- `ROWAN_API_KEY` is present in the environment.
- `OPENAI_API_KEY` is present in the environment.
- OpenAI SDK is installed in `.venv` and a redacted model-list auth smoke test passed.
- Project-local MCP config exists at `.mcp.json`.
- Convoke Bio MCP endpoint is configured as `convoke-bio` with URL `https://mcp.convoke.bio/mcp`.

## Partially Ready

- AWS CLI and boto3 are installed in the project virtualenv.
- AWS credentials are not available to the current shell: `aws sts get-caller-identity` returns `Unable to locate credentials`.
- S3 upload is therefore not ready until AWS credentials/profile are provided.

## Not Required For Current Demo

- Direct `ONEPOT_API_KEY` is not present. OnePot is still visible through Muni, which is sufficient for the current hack lane.
- `CONVOKE_MCP_TOKEN` is not required unless using a client flow that cannot complete Convoke OAuth automatically.
- AWS is optional for the current local demo; do not claim AWS resources are configured until `sts get-caller-identity` succeeds.

## Safe Recheck Commands

```bash
cd /Users/byron/projects/inbox/biocustody-stateshift-aws-bootstrap-v0.2.0
source .venv/bin/activate
kaggle kernels status biobitworks/bio-delta-g-cpjump1-sweep
kaggle kernels output biobitworks/bio-delta-g-cpjump1-sweep -p runs/kaggle_output -o
python scripts/check_env.py
python scripts/check_hackathon_integrations.py
muni whoami
muni balance --json
muni tool onepot --inputs
muni tool rowan_descriptors --inputs
aws sts get-caller-identity
```
