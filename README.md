# BioCustody — Cross-Device FCO/FCG Terminal on sauna.ai

Stanford × DeepMind Hackathon 2026 submission. Deployed at https://biocustody-n6iqdjsn.sauna.new/.

## What's here

This is the sauna.ai app source — the central custody registry that aggregates a union Fractal Custody Graph (FCG) across web, Android (ExecuTorch + Gemma 4 QAT-mobile), Replit, and AI agent turns, all bound to a single Ed25519 public-key fingerprint (SHA-256): `903fec780c8219cccec286d845d3f58da70fa3b2969a8ad4a77bfc58fa1a8c35`.

## What's in BioCustody

BioCustody shows **chain of custody across heterogeneous devices** using the FCO v3 protocol from the FCO/FCG Zenodo publication. Every seal, chat turn, and quantized-model inference is content-addressed and bound to the same public key.

- `/api/seal` — web form seals a new sample (sequence + GPS + custodian) and binds it to the public key.
- `/api/sync` — Android / Replit / Antigravity clients POST pre-sealed FCO envelopes to this endpoint.
- `/api/turn` and `/api/chat` — every chat turn and every Gemini copilot reply becomes an FCO. The Sauna agent itself appears in the conversation FCG.
- `/api/verify` — server recomputes the MMR over all leaves and returns the canonical root.
- `/api/tts` — ElevenLabs proxy for accessibility (blind / deaf multimodal): reads the live BILN transcript aloud.

## Files

- `app.md` — manifest + README
- `src/handler.ts` — Hono backend, FCO v3 primitives + MMR, Gemini proxy, ElevenLabs /api/tts
- `src/lib/fco.ts` — file FCO root, conversation leaf hash, MMR graph root
- `src/schema.ts` — Drizzle SQLite schema (fcos + fcg_state)
- `src/App.tsx` — React SPA with Dashboard / Capture / Folding / Chat, live BILN transcript, peptide analysis, ElevenLabs listen button
- `public/index.html` + `public/style.css` — Material 3 glassmorphic mobile-first UI
- `migrations/0000_init.sql` — initial schema

## Three tracks

1. **sauna.ai** (this repo) — `biocustody-n6iqdjsn.sauna.new`
2. **Replit** — parallel Express host that POSTs FCOs to `/api/sync` on the sauna.ai server
3. **Android Kotlin / Jetpack Compose + ExecuTorch** — sealed locally with the same key, posts to `/api/sync`

## Verify

```bash
curl -s https://biocustody-n6iqdjsn.sauna.new/api/verify | jq
# { leaf_count, computed_root, by_device }
```

## Seal a sample from any device

```bash
curl -X POST https://biocustody-n6iqdjsn.sauna.new/api/sync \
  -H "Content-Type: application/json" \
  -d '{
    "object_id": "sha256:demo001",
    "object_type": "field_sample_sealed",
    "content_leaf": "ab12...",
    "fco_root": "cd34...",
    "leaf_hash": "ef56...",
    "node_id": "curl-demo/sample/2026-07-19T20:00:00Z",
    "parents_json": "[]",
    "envelope_json": "{}",
    "payload_preview": "demo sample",
    "claim_ceiling": "Demo sync.",
    "device_id": "curl-demo",
    "device_type": "cloud",
    "created_locally_at_utc": "2026-07-19T20:00:00.000Z"
  }'
```

## Agent contract

https://biocustody-n6iqdjsn.sauna.new/llms.txt

## Author

Byron P. Lee · biobitworks · 2026-07-19 · Stanford × DeepMind Hackathon
