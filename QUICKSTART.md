# Quickstart — tonight vs. hackathon day

## Tonight: make the core deterministic

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[demo]"
python scripts/check_env.py
pytest -q
python scripts/demo_synthetic.py
streamlit run ui/app.py
```

Expected outcome: the app runs without AWS and shows:

- a reference state cloud;
- a perturbed state;
- ranked counter-perturbation candidates;
- exact FCO hashes;
- a claim ceiling;
- a tamper demonstration.

## Optional tonight: muni

```bash
pipx install muni
muni login
muni whoami
muni tools -q onepot
muni tools -q rowan
```

Use `muni tool <tool-name> --inputs` before submitting anything. Keep spending explicit.

## Optional tonight: onepot direct client

Set the key locally; never commit it:

```bash
export ONEPOT_API_KEY='...'
pip install onepot
python scripts/query_onepot.py 'CC(=O)Oc1ccccc1C(=O)O'
```

Do not publish CORE results unless your access terms permit it.

## Optional tonight: BILN/HELM

Use the isolated pyPept environment because pyPept's documented environment is older than the main AWS/muni Python stack.

```bash
conda env create -f envs/pypept/environment.yml
conda activate biocustody-pypept
python scripts/convert_biln.py \
  --biln 'P-E-P-T-I-D-E' \
  --prefix runs/local/peptide_demo
```

The script emits canonical SMILES and SDF while preserving the original BILN in the sidecar manifest.

## Hackathon morning

1. Verify AWS credentials and Bedrock model access.
2. Keep the local demo working before deployment.
3. Connect HCLS MCPs / Strands agent.
4. Put the deterministic StateShift/FCO tool behind Lambda or AgentCore Gateway.
5. Add policy/observability.
6. Run evaluations.
7. Add Neptune only if time remains.
