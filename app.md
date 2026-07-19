---
name: biocustody
description: "BioCustody — cross-device Fractal Custody Object terminal. Each FCO is sealed to the 903fec78 key by every party in the chain (Android phone, web browser, Gemini copilot, sauna.ai agent) and the server aggregates the union FCG so chain of custody is verifiable across all of them."
manifest_version: 1
enabled: true
visibility: public
---

# BioCustody — Cross-Device Chain of Custody Terminal

A Sauna App that proves chain of custody across heterogeneous devices, agents, and
models. Every FCO is content-addressed (SHA-256), bound to the Ed25519 public key
fingerprint `903fec780c8219cccec286d845d3f58da70fa3b2969a8ad4a77bfc58fa1a8c35`,
and appended to a Merkle Mountain Range (MMR) graph. The graph root recomputes
on every server change, so any tampering, missing node, or key mismatch fails closed.

## What makes it "cross-device"

Every FCO stored in `fcos` carries:

- `device_id` — a stable id per device (e.g. `web-demo`, `android-001`, `replit-prod`)
- `device_type` — `web` | `android` | `replit` | `cloud` | `agent`
- `created_locally_at_utc` — the timestamp the device sealed it
- `synced_at_utc` — the timestamp sauna.ai received it

The Dashboard shows the per-device breakdown. The FCG root is the MMR over **all**
leaves across **all** devices, sorted by `created_locally_at_utc`. Sealing a new
FCO from the web triggers an immediate root recompute; `/api/sync` lets an Android
phone POST a pre-sealed FCO and see the root move.

## What makes the model "real"

The Folding screen loads `Xenova/esm2_t6_8M_UR50D` (8M-parameter ESM2) via
Transformers.js / onnxruntime-web as an int8 quantized ONNX model. It runs locally
in the browser, shows per-token latency, emits the actual embedding vector, and
renders a real cosine-similarity contact-map heatmap derived from the embeddings.
This is the same shape as a quantized ESMFold/AlphaFold contact-map predictor but
in a browser-runnable size. The Android target uses ExecuTorch on the Hexagon NPU;
the web demo uses ONNX Runtime Web. Both are quantified local inference.

## What makes the agent part of the FCG

Every chat turn is a `turn` FCO bound to the same `903fec78` key. The Sauna agent's
replies appear as `agent` role turns in the union FCG, alongside human investigator
turns and `/api/chat` Gemini responses. The conversation FCG is the substrate that
proves the chain: human, Gemini, and Sauna agent are all parties on the same key.

## Endpoints

| Method | Path | Body | Returns |
|--------|------|------|---------|
| GET    | `/`              | — | mobile Material 3 SPA |
| GET    | `/llms.txt`      | — | plain text agent contract |
| POST   | `/api/seed-initial` | — | idempotent first-run seed of the 5 conversation turns + 3 synthetic Android FCOs |
| POST   | `/api/seal`      | `{name, sequence, gps_lat, gps_lng, custodian, device_id?}` | `{fco_root, object_id, leaf_count, fcg_root}` |
| POST   | `/api/sync`      | `{object_id, object_type, content_leaf, op_leaf, parents, envelope, device_id, device_type, created_locally_at_utc, claim_ceiling}` | `{ok, fcg_root, leaf_count}` |
| POST   | `/api/turn`      | `{role, content, device_id?}` | `{fco_root, fcg_root}` |
| POST   | `/api/chat`      | `{message, history?}` | `{reply, fcg_root, threat_warning?}` (proxy to Gemini via the sauna.ai `google_gemini` account) |
| GET    | `/api/live`      | — | `{leaf_count, merkle_root, last_12_leaves, by_device, server_time_utc}` |
| GET    | `/api/graph`     | — | `{nodes:[…], count}` |
| GET    | `/api/verify`    | — | `{leaf_count, computed_root, by_device}` (server recomputes MMR) |
| GET    | `/api/fco/:id`   | — | `{object_id, envelope, payload_preview, device_id, device_type, created_locally_at_utc}` |

## Bootstrap / external state

- **Gemini API**: pinned at deploy via the sauna.ai `google_gemini` connection
  (`biobitworks@gmail.com`). The chat endpoint proxies to `gemini-1.5-flash` with
  the FCO system prompt (903fec78 fingerprint + ricin/toxin threat classification).
  If the connection is missing, chat falls back to a deterministic mock and logs
  a `mock_chat` FCO so the chain stays verifiable.
- **First-run seed**: `/api/seed-initial` is called by the SPA on mount. It writes
  the 5 original conversation turns from `conversations/conversations_fcg.json`
  plus 3 synthetic Android FCOs to demonstrate the cross-device breakdown. The
  seed is idempotent — re-running with the same `object_id` is a no-op.
- **Static model files**: the ESM2 int8 quantized model is loaded at runtime from
  the Hugging Face CDN under `Xenova/esm2_t6_8M_UR50D` (cached by the browser).

## Verify

```bash
curl -s https://<app-id>.sauna.new/api/verify | jq
```

Returns `{leaf_count, computed_root, by_device}`. The Dashboard's
"FCG root matches server" indicator flips red on mismatch.
