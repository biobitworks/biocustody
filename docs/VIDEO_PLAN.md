# Video plan

## Recommended deliverable

Record a **90-second primary demo** plus an optional **3-minute technical cut**.

Use real screen capture. A generated narration is optional and should not replace showing the working system.

## 90-second shot list

### 0–10s — problem

Visual: reference-cloud text/plot.

Voice:
> Biology changes continuously, but audit systems and AI claims are discrete. We need to know both whether the bytes changed and whether the scientific state actually changed.

### 10–25s — state model

Visual: controls → reference cloud → perturbation outside.

Voice:
> Every observation gets an exact cryptographic identity. Separately, a versioned statistical model determines whether it remains within the reference state.

### 25–40s — candidate ranking

Visual: ranking table, candidate A rises to top.

Voice:
> We then rank independently measured compound profiles by how strongly they oppose the perturbation direction. This is a predicted counter-perturbation—not an experimental rescue claim.

### 40–55s — molecular bridge

Visual: BILN → SMILES / candidate card.

Voice:
> Small molecules travel as canonical SMILES. Complex peptides can remain in BILN or HELM, with pyPept producing derived SMILES and SDF representations under the same custody route.

### 55–70s — FCO graph

Visual: source → state → ranking → claim.

Voice:
> Every source, transformation, tool result, and claim becomes a linked custody object, so the system can show exactly why a candidate was ranked and how strong a claim is permitted.

### 70–82s — tamper

Visual: change one value → verification failure.

Voice:
> Change one upstream object and the route diverges. The dependent claim is no longer admissible until it is recomputed.

### 82–90s — AWS

Visual: local core → AgentCore.

Voice:
> On AWS, the research agent can propose a claim, but deterministic policy decides whether it can be published.

## ElevenLabs

Use only after the final script is frozen.

The repo includes:

```bash
pip install -e ".[voice]"
python scripts/video_voiceover.py
```

Store the voice ID and API key only in `.env`.

## Sauna.ai

Treat Sauna as optional presentation/UI acceleration only.

Do not make it a critical scientific dependency. If used, give it the local API/JSON outputs and reproduce the same deterministic results already available in the local Streamlit demo.
