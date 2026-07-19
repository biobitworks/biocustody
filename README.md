# BioCustody — Cross-Device Chain of Custody Terminal

**Stanford × DeepMind Hackathon 2026 Submission**  
- Deployed Web Prototype: [https://biocustody-n6iqdjsn.sauna.new/](https://biocustody-n6iqdjsn.sauna.new/)
- Code Repository (this repo): [https://github.com/biobitworks/biocustody](https://github.com/biobitworks/biocustody)
- FCG Root (Sealed Submission): `7acd4129f15bd1f237aad2b0c5cf07e6e41124ee7061d821b9cc734a4c0a445a`
- Public Key Fingerprint (Ed25519 SHA-256): `903fec780c8219cccec286d845d3f58da70fa3b2969a8ad4a77bfc58fa1a8c35`
- Submitter: **Byron P. Lee** (Founder, Cellico.Bio) | `byron@biobitworks.com`

---

## 1. Project Goal & Executive Summary

**BioCustody** is a decentralized data provenance and remote biosurveillance platform that secures biological fieldwork and pathogen tracking. By combining lightweight, quantized structural protein folding running locally on Android devices (using ExecuTorch) with cryptographic **Fractal Custody Objects (FCOs)** bound to an investigator's Ed25519 key, BioCustody creates a tamper-proof chain of custody (Fractal Custody Graph - FCG) for biosecurity threat detection—completely offline.

This repository contains the **sauna.ai Track / Google AI Studio & Cloud Run** hosted prototype. It acts as the central administrative registry where auditors view the overall graph history, use Gemini to check sequence vulnerabilities, and verify the cryptographic integrity of pre-sealed FCOs synced from remote devices (such as Android phones running ExecuTorch or parallel Replit instances).

---

## 2. Technical Audit: What is Live vs. Trajectory

We believe in absolute technical honesty. Here is the exact audit of what is implemented and runnable for judges versus what is documented as a planned trajectory:

### 🟢 Fully Implemented & Live (Run them now!)
- **Cross-Device FCG Aggregation (MMR):** The server aggregates FCOs from multiple devices (`device_id` + `device_type` present in SQLite). Tap the Dashboard to see nodes from `web-demo`, `byron-mbp` (Mac), `antigravity-codx`, `android-001` (Snapdragon phone), and `sauna-agent` (Sauna AI agent).
- **The FCG substrate is itself the transcript:** In accordance with the FCG principle *"you are also part of the FCG as an FCO"*, every single message, prompt, and intermediate agent step in this session is signed, content-addressed, and appended as an FCO turn in the live graph.
- **Local ESM2 ONNX Inference:** The Folding screen loads `Xenova/esm2_t6_8M_UR50D` (8M-parameter ESM2 quantized to int8, 7.7MB size) **directly from this origin's local `/models/` path** (zero CDN dependencies). It runs real-time local inference in your browser Web Assembly runtime and outputs the hidden-state embeddings.
- **Real-Time Per-Token Transcript:** As the ESM2 model runs in your browser, a live terminal panel streams the per-token output: position, residue character, cumulative ms, and the `sha256[:8]` of the per-token embedding slice.
- **pyPept-style Peptide Analysis:** The Folding screen computes real-world peptide properties live: residues, Molecular Weight (Da), Isoelectric Point (pI), GRAVY hydropathy (Kyte-Doolittle scale), and predicted helix/sheet propensities (Chou-Fasman-style residue propensities).
- **Real-Time BILN → ElevenLabs Audio (Accessibility):** Tap **Listen (ElevenLabs)** or **Speak Analysis** on the Folding screen. The app calls `/api/tts` (which proxies ElevenLabs `ys3XeJJA4ArWMhRpcX1D` / `RXIcu418WGXrG1TSbJx2` via Sauna) to convert the live BILN transcript and peptide properties into speech, enabling fully-voice narration for blind or deaf accessibility.
- **Real AlphaFold DB pLDDT Integration:** Tap "Run Local Quantized Model" on the Folding screen. The backend `/api/plddt` endpoint queries the public AlphaFold Database API for the sequence, downloads the latest v6 PDB, parses the CA-atom B-factor column, and returns the **real per-residue pLDDT confidence array** (mean score displayed, e.g. `96.6% (AF DB v6)`).
- **3Dmol.js WebGL Visualization:** Downloads and renders the canonical 3D structures from AlphaFold (pdb:1gfl for GFP, pdb:1rtc for Ricin A-Chain) in gorgeous WebGL ribbon cartoons.
- **Google AI Studio (Gemini) Copilot Proxy:** The Copilot screen calls Google AI Studio (`gemini-1.5-flash`) via the Sauna connection and enforces the biosecurity system prompt (fingerprint 903fec78... + toxin containment warnings).

### 🟡 Documented Trajectory (Future Plans / Mocked)
- **On-Device ExecuTorch (Android Track):** The Android Jetpack Compose codebase lives in the parallel `/android` folder. It is designed to compile and run Gemma 4 E2B-it-qat-mobile-ct on the Qualcomm Hexagon NPU natively via ExecuTorch. This is documented and use-case proposed, not built into this web prototype.
- **Google Drive / Gmail private-key Vault:** As documented in the *Future Architecture* section of our submission package, we propose using Google Drive's `changes.list` as the FCG event-bus and a Google Drive folder as the private-key vault, integrated with Gmail/KG indexing.
- **AlphaTensor, Phenaki, AlphaProteo, USM, DolphinGemma:** Surfaced as display-only model/research artifacts in the Folding screen to contextualize the scientific lineage. Not actively executed.

---

## 3. Evidentiary Claim Ceiling & Determinism Matrix

To prevent circular validation and trust-by-storage, every operation in BioCustody's runtime has an explicit claim ceiling:

| Operation | Type | Claim Ceiling |
|---|---|---|
| **FCO/FCG Merkle Roots** | `[DETERMINISTIC]` | Proves exact file bytes, key binding, and sequence order. Mismatch fails closed. Does not prove scientific correctness of the sequence or safety. |
| **Peptide Heuristics** | `[DETERMINISTIC]` | Computes molecular mass and GRAVY hydropathy exactly from physical residue coefficients. |
| **ESM2 Embeddings** | `[DETERMINISTIC]` | Emits exact local WASM/ONNX hidden states. |
| **pLDDT Scores** | `[PROBABILISTIC]` | AlphaFold DB model predictions. Represents statistical structural confidence, not empirical physical stability. |
| **Gemini Copilot Answers** | `[PROBABILISTIC]` | Generative AI outputs. Subject to hallucination; must be treated as advisory; must not bypass physical containment rules. |
| **Narrations & Images** | `[CREATIVE]` | ElevenLabs / Imagen outputs. Generated for human accessibility and illustration; carries no scientific or empirical proof. |

---

## 4. Lineage & Citations

### Original (Prior Art)
1. **FCO / FCG v3.0.0 Spec (Zenodo Preprint):** [https://doi.org/10.5281/zenodo.21210575](https://doi.org/10.5281/zenodo.21210575) — Spec for the FCO v3 protocol (MMR, file root = sha256). Author: Byron P. Lee.
2. **voiceworks (Sauna App):** [https://voiceworks-ygitm4zl.sauna.new/](https://voiceworks-ygitm4zl.sauna.new/) — ElevenLabs × Sauna Hack Night (2026-07-16). Prior FCO voice vault. Reused MMR / RFC-6962 primitives.
3. **biobitworks/phonebio (Android Repo):** [https://github.com/biobitworks/phonebio.git](https://github.com/biobitworks/phonebio.git) — On-device bio sealing + telemetry.
4. **biobitworks/glasswork (Repo):** [https://github.com/biobitworks/glasswork.git](https://github.com/biobitworks/glasswork.git) — Multi-model evaluation scoring with FCO.
5. **AlphaFold (DeepMind):** [https://alphafold.ebi.ac.uk/](https://alphafold.ebi.ac.uk/) — Canonical protein structure source.
6. **Gemma 4 QAT (DeepMind):** [gemma-4-qat-mobile](https://huggingface.co/collections/google/gemma-4-qat-mobile) — QAT-trained mobile Gemma 4.
7. **pyPept (Boehringer Ingelheim):** [https://github.com/Boehringer-Ingelheim/pyPept.git](https://github.com/Boehringer-Ingelheim/pyPept.git) — Reference for peptide property heuristics.

---

## 5. Verify the Proof Yourself

Judges can verify the FCG closed-loop status and recompute the Merkle Mountain Range root from the command line:

```bash
# 1. Fetch current live FCG verify status
curl -s https://biocustody-n6iqdjsn.sauna.new/api/verify | jq

# 2. Confirm the root matches the live touch log
curl -s https://biocustody-n6iqdjsn.sauna.new/api/live | jq .merkle_root

# 3. Read the agent contract at /llms.txt
curl -s https://biocustody-n6iqdjsn.sauna.new/llms.txt
```

---
*Built for the Stanford × DeepMind Hackathon, July 19, 2026. Author: Byron P. Lee. Deployed via Sauna.*
