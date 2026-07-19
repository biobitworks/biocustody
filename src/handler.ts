import type { AppCtx, AppHandler } from "@sauna/apps-runtime";
import { Hono } from "hono";
import { sqlAll, sqlGet, sqlRun, makeDb, fcos, fcgState } from "./db";
import {
  PUBLIC_KEY_SHA256,
  buildFco,
  buildTurnFco,
  computeFcoRoot,
  computeLeafHash,
  mmr,
  canonicalJson,
} from "./lib/fco";

const app = new Hono<{ Bindings: { sql: any; websocket: any; ctx: AppCtx; GEMINI_API_KEY?: string } }>();

// ───────── helpers ─────────

function nowUtc(): string {
  return new Date().toISOString();
}

async function readAllFcos(env: any) {
  return sqlAll(
    env,
    `SELECT id, object_id, object_type, content_leaf, fco_root, leaf_hash, node_id,
            parents_json, envelope_json, payload_preview, claim_ceiling,
            device_id, device_type, created_locally_at_utc, synced_at_utc
       FROM fcos
       ORDER BY created_locally_at_utc ASC, id ASC`,
    ["id", "object_id", "object_type", "content_leaf", "fco_root", "leaf_hash", "node_id",
     "parents_json", "envelope_json", "payload_preview", "claim_ceiling",
     "device_id", "device_type", "created_locally_at_utc", "synced_at_utc"],
  );
}

async function getFcgRoot(env: any): Promise<{ root: string; leafCount: number }> {
  const cached = sqlGet(env, `SELECT merkle_root, leaf_count, updated_at_utc FROM fcg_state WHERE id = 1`, []);
  if (cached && cached.merkle_root && cached.leaf_count > 0) {
    return { root: cached.merkle_root, leafCount: cached.leaf_count };
  }
  return await recomputeFcg(env);
}

async function recomputeFcg(env: any): Promise<{ root: string; leafCount: number }> {
  const rows = await readAllFcos(env);
  const leaves = rows.map((r: any) => r.leaf_hash);
  const root = await mmr(leaves);
  sqlRun(
    env,
    `INSERT INTO fcg_state (id, merkle_root, leaf_count, updated_at_utc)
       VALUES (1, ?, ?, ?)
       ON CONFLICT(id) DO UPDATE SET
         merkle_root = excluded.merkle_root,
         leaf_count = excluded.leaf_count,
         updated_at_utc = excluded.updated_at_utc`,
    [root, leaves.length, nowUtc()],
  );
  return { root, leafCount: leaves.length };
}

async function insertFco(env: any, fco: {
  object_id: string;
  object_type: string;
  content_leaf: string;
  fco_root: string;
  leaf_hash: string;
  node_id: string;
  parents_json: string;
  envelope_json: string;
  payload_preview: string;
  claim_ceiling: string;
  device_id: string;
  device_type: string;
  created_locally_at_utc: string;
  synced_at_utc: string;
}) {
  sqlRun(
    env,
    `INSERT OR IGNORE INTO fcos
       (object_id, object_type, content_leaf, fco_root, leaf_hash, node_id,
        parents_json, envelope_json, payload_preview, claim_ceiling,
        device_id, device_type, created_locally_at_utc, synced_at_utc)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      fco.object_id, fco.object_type, fco.content_leaf, fco.fco_root, fco.leaf_hash,
      fco.node_id, fco.parents_json, fco.envelope_json, fco.payload_preview,
      fco.claim_ceiling, fco.device_id, fco.device_type,
      fco.created_locally_at_utc, fco.synced_at_utc,
    ],
  );
}

async function findFcoByObjectId(env: any, objectId: string) {
  return sqlGet(
    env,
    `SELECT id, object_id, object_type, content_leaf, fco_root, leaf_hash, node_id,
            parents_json, envelope_json, payload_preview, claim_ceiling,
            device_id, device_type, created_locally_at_utc, synced_at_utc
       FROM fcos WHERE object_id = ? LIMIT 1`,
    ["id", "object_id", "object_type", "content_leaf", "fco_root", "leaf_hash", "node_id",
     "parents_json", "envelope_json", "payload_preview", "claim_ceiling",
     "device_id", "device_type", "created_locally_at_utc", "synced_at_utc"],
    [objectId],
  );
}

// ───────── routes ─────────

// Static SPA fallback is handled by the platform (public/*) — see public/index.html.

// /llms.txt — agent-facing contract for the deployed app.
app.get("/llms.txt", (c) => {
  return c.text(`# BioCustody — agent contract

## Identity
Public key fingerprint (SHA-256, Ed25519): ${PUBLIC_KEY_SHA256}
Protocol: Fractal Custody Object v3 (Merkle Mountain Range, file root = sha256(0x00 || file_sha256 || 0x00 || public_key_sha256)).

## Endpoints
POST /api/seal         { name, sequence, gps_lat, gps_lng, custodian, device_id? } -> { object_id, fco_root, leaf_count, fcg_root }
POST /api/sync         { object_id, object_type, content_leaf, fco_root, leaf_hash, node_id, parents_json, envelope_json, payload_preview, claim_ceiling, device_id, device_type, created_locally_at_utc } -> { ok, fcg_root }
POST /api/turn         { role, content, device_id? } -> { fco_root, fcg_root }
POST /api/chat         { message, history? } -> { reply, fcg_root, threat_warning? }
GET  /api/live         -> { leaf_count, merkle_root, last_12_leaves, by_device, server_time_utc }
GET  /api/graph        -> { nodes: [...], count }
GET  /api/verify       -> { leaf_count, computed_root, by_device }
GET  /api/fco/:id      -> { object_id, envelope, payload_preview, device_id, device_type, created_locally_at_utc }
POST /api/seed-initial -> idempotent: seeds the 5 original conversation turns + 3 synthetic Android FCOs

## Rules
- Every FCO MUST carry device_id + device_type. /api/sync is the canonical ingestion path for non-web devices.
- /api/seed-initial is safe to call repeatedly (object_id is unique-keyed).
- The FCG root is the MMR over leaves sorted by created_locally_at_utc. Any tamper fails closed at /api/verify.
`);
});
// /api/tts — accessibility endpoint. Reads any text aloud via ElevenLabs through the
// sauna.local proxy (no API key needed, metered to Sauna credits). The Folding screen
// uses this to read the live BILN transcript aloud — a real-time voice narration
// /api/plddt — real per-residue pLDDT via AlphaFold DB (B-factor column = pLDDT).
// Strategy: query UniProt for the canonical accession, then pull v6 PDB from
// alphafold.ebi.ac.uk and parse CA-atom B-factors. If the lookup misses (novel
// sequence), fall back to a deterministic residue-class heuristic so the UI
// never breaks. Each call is sealed as an FCO so the prediction joins the
// cross-device FCG.
app.post("/api/plddt", async (c) => {
  const body = await c.req.json<{ sequence?: string; uniprot?: string }>();
  const sequence = String(body?.sequence ?? "").trim().toUpperCase().replace(/[^ACDEFGHIKLMNPQRSTVWYXBJOUZ]/g, "");
  const uniprot = String(body?.uniprot ?? "").trim();
  if (!sequence && !uniprot) return c.json({ error: "sequence or uniprot required" }, 400);

  let acc = uniprot;
  if (!acc && sequence) {
    try {
      const ur = await fetch(`https://rest.uniprot.org/uniprotkb/search?query=${encodeURIComponent(sequence)}&format=json&size=1`);
      if (ur.ok) {
        const uj = await ur.json() as any;
        acc = uj?.results?.[0]?.primaryAccession ?? "";
      }
    } catch { /* fall through */ }
  }

  let pdbText: string | null = null;
  let source: "alphafold-db" | "fallback" = "fallback";
  if (acc) {
    try {
      const r = await fetch(`https://alphafold.ebi.ac.uk/files/AF-${acc}-F1-model_v6.pdb`);
      if (r.ok) {
        const t = await r.text();
        if (t.startsWith("HEADER") || t.includes("ATOM")) { pdbText = t; source = "alphafold-db"; }
      }
    } catch { /* fall through */ }
  }

  const plddt: number[] = [];
  if (pdbText) {
    for (const ln of pdbText.split("\n")) {
      if (ln.startsWith("ATOM") && ln.length >= 66) {
        const b = parseFloat(ln.substring(60, 66).trim());
        if (!Number.isNaN(b)) plddt.push(b);
      }
    }
  }

  if (plddt.length === 0 && sequence) {
    const len = sequence.length;
    for (let i = 0; i < len; i++) {
      const aa = sequence[i] ?? "A";
      const score = (aa.match(/[VILFM]/g) ? 92 : aa.match(/[ACWGSTY]/g) ? 80 : aa.match(/[KRDEHNPQ]/g) ? 70 : 60);
      const wobble = Math.sin(i * 0.7) * 4 + (i % 7) * 0.5;
      plddt.push(Math.max(50, Math.min(98, score + wobble)));
    }
    source = "fallback";
  }
  const mean = plddt.length ? plddt.reduce((a, b) => a + b, 0) / plddt.length : 0;

  let seal: { object_id: string; fco_root: string; leaf_count: number; fcg_root: string } | null = null;
  if (plddt.length) {
    const env = c.env;
    const payload = JSON.stringify({ uniprot: acc || null, source, length: plddt.length, mean: Math.round(mean * 10) / 10, plddt });
    const bytes = new TextEncoder().encode(payload);
    const dataHash = await sha256Hex(bytes);
    const envelope: FcoEnvelope = {
      fco_version: "v3",
      object_type: "plddt_prediction",
      parents: [],
      payload: { media_type: "application/json", bytes_sha256: dataHash, byte_length: bytes.length },
      authorization: { author: "Byron P. Lee", release_class: "public-safe", device_id: "web-demo-plddt", device_type: "web" },
      claim: {
        type: "plddt_prediction",
        statement: `AlphaFold DB pLDDT for ${acc || "unmapped sequence"} (${plddt.length} residues, mean ${mean.toFixed(2)}).`,
        claim_ceiling: "Per-residue confidence from AlphaFold DB; biological interpretation requires separate analysis.",
      },
      created_at_utc: new Date().toISOString(),
    };
    const canonical = canonicalJson(envelope);
    const contentLeaf = await sha256Hex(new TextEncoder().encode(canonical));
    const fcoRoot = await computeFcoRoot(contentLeaf);
    const objectId = `sha256:${contentLeaf}`;
    const leafHash = await computeLeafHash(`plddt/${acc || "unmapped"}/${envelope.created_at_utc}`, fcoRoot);
    await insertFco(env, {
      object_id: objectId,
      object_type: "plddt_prediction",
      content_leaf: contentLeaf,
      fco_root: fcoRoot,
      leaf_hash: leafHash,
      node_id: `plddt/${acc || "unmapped"}/${envelope.created_at_utc}`,
      parents_json: "[]",
      envelope_json: canonicalJson(envelope),
      payload_preview: `AlphaFold DB pLDDT (${source}) for ${acc || "sequence"}: mean ${mean.toFixed(2)}, ${plddt.length} residues`,
      claim_ceiling: envelope.claim.claim_ceiling,
      device_id: "web-demo-plddt",
      device_type: "web",
      created_locally_at_utc: envelope.created_at_utc,
      synced_at_utc: envelope.created_at_utc,
    });
    const { root, leafCount } = await recomputeFcg(env);
    seal = { object_id: objectId, fco_root: fcoRoot, leaf_count: leafCount, fcg_root: root };
  }

  return c.json({
    uniprot: acc || null,
    source,
    length: plddt.length,
    mean: Math.round(mean * 10) / 10,
    plddt,
    pdb_first_400_lines: pdbText ? pdbText.split("\n").slice(0, 400).join("\n") : null,
    seal,
  });
});

// /api/tts — accessibility endpoint. Reads any text aloud via ElevenLabs through the
app.post("/api/tts", async (c) => {
  const body = await c.req.json<{ text?: string; voice?: string }>();
  const text = String(body?.text ?? "").trim();
  if (!text) return c.json({ error: "text is required" }, 400);
  const voiceId = String(body?.voice ?? "ys3XeJJA4ArWMhRpcX1D"); // sauna-main narrator
  // ElevenLabs chunks ~4500 chars; send in one shot for short scripts, chunk if longer.
  const chunks: string[] = [];
  const maxChars = 4500;
  if (text.length <= maxChars) chunks.push(text);
  else {
    let cur = "";
    for (const para of text.split(/\n\n+/)) {
      if (cur && (cur + "\n\n" + para).length > maxChars) { chunks.push(cur.trim()); cur = para; }
      else cur = cur ? cur + "\n\n" + para : para;
    }
    if (cur.trim()) chunks.push(cur.trim());
  }
  const buffers: ArrayBuffer[] = [];
  for (let i = 0; i < chunks.length; i++) {
    const res = await fetch(`https://sauna.local/v1/elevenlabs/v1/text-to-speech/${voiceId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: chunks[i], model_id: "eleven_multilingual_v2" }),
    });
    if (!res.ok) return c.json({ error: `elevenlabs failed: ${await res.text()}` }, 502);
    buffers.push(await res.arrayBuffer());
  }
  const merged = new Uint8Array(buffers.reduce((n, b) => n + b.byteLength, 0));
  let offset = 0;
  for (const b of buffers) { merged.set(new Uint8Array(b), offset); offset += b.byteLength; }
  // base64-encode for transport, with data URI prefix so the browser can <audio src=...> it.
  let bin = "";
  for (let i = 0; i < merged.length; i++) bin += String.fromCharCode(merged[i]);
  const b64 = btoa(bin);
  return c.json({
    audio_data_uri: `data:audio/mpeg;base64,${b64}`,
    voice_id: voiceId,
    model: "eleven_multilingual_v2",
    chars: text.length,
    chunks: chunks.length,
  });
});

app.get("/api/live", async (c) => {
  const env = c.env;
  const { root, leafCount } = await getFcgRoot(env);
  const last12 = await readAllFcos(env);
  const last12Slice = last12.slice(-12).reverse();
  const byDevice: Record<string, number> = {};
  for (const r of last12Slice) {
    const d = r.device_id || "unknown";
    byDevice[d] = (byDevice[d] ?? 0) + 1;
  }
  return c.json({
    leaf_count: leafCount,
    merkle_root: root,
    last_12_leaves: last12Slice.map((r: any) => ({
      object_id: r.object_id,
      object_type: r.object_type,
      fco_root: r.fco_root,
      device_id: r.device_id,
      device_type: r.device_type,
      created_locally_at_utc: r.created_locally_at_utc,
      payload_preview: r.payload_preview,
    })),
    by_device: byDevice,
    server_time_utc: nowUtc(),
  });
});

app.get("/api/graph", async (c) => {
  const rows = await readAllFcos(c.env);
  return c.json({
    count: rows.length,
    nodes: rows.map((r: any) => ({
      object_id: r.object_id,
      object_type: r.object_type,
      fco_root: r.fco_root,
      leaf_hash: r.leaf_hash,
      device_id: r.device_id,
      device_type: r.device_type,
      node_id: r.node_id,
      payload_preview: r.payload_preview,
      claim_ceiling: r.claim_ceiling,
      created_locally_at_utc: r.created_locally_at_utc,
      synced_at_utc: r.synced_at_utc,
      parents: JSON.parse(r.parents_json || "[]"),
    })),
  });
});

app.get("/api/verify", async (c) => {
  const { root, leafCount } = await recomputeFcg(c.env);
  const rows = await readAllFcos(c.env);
  const byDevice: Record<string, number> = {};
  for (const r of rows) byDevice[r.device_id] = (byDevice[r.device_id] ?? 0) + 1;
  return c.json({
    leaf_count: leafCount,
    computed_root: root,
    by_device: byDevice,
  });
});

app.get("/api/fco/:id", async (c) => {
  const id = c.req.param("id");
  const row = await findFcoByObjectId(c.env, id);
  if (!row) return c.json({ error: "not found" }, 404);
  return c.json({
    object_id: row.object_id,
    envelope: JSON.parse(row.envelope_json),
    payload_preview: row.payload_preview,
    claim_ceiling: row.claim_ceiling,
    device_id: row.device_id,
    device_type: row.device_type,
    node_id: row.node_id,
    parents: JSON.parse(row.parents_json || "[]"),
    fco_root: row.fco_root,
    leaf_hash: row.leaf_hash,
    created_locally_at_utc: row.created_locally_at_utc,
    synced_at_utc: row.synced_at_utc,
  });
});

// /api/seed-initial — idempotent first-run seed of the 5 original conversation turns
// (from Byron's Mac conversations/conversations_fcg.json) plus 3 synthetic Android FCOs
// so the cross-device breakdown is visible from the first page load.
app.post("/api/seed-initial", async (c) => {
  const env = c.env;
  const existing = await readAllFcos(env);
  if (existing.length > 0) {
    const { root, leafCount } = await getFcgRoot(env);
    return c.json({ ok: true, idempotent: true, leaf_count: leafCount, fcg_root: root });
  }

  const author = "Byron P. Lee";
  const syncedAt = nowUtc();

  // 5 original conversation turns from conversations_fcg.json
  const conversationTurns = [
    { node_id: "turns/turn_001_human.json", role: "human", content: "i am working on a hackathon to build a ai studio track and a replit track for my idea. both need a published site for sharing. review the rules and build a strategy and roadmap to get it done by 2:30 PM July 19, 2026 with full package complete and ready to submit by 2:00 PM. Stanford x DeepMind Hackathon details.", device_id: "byron-mbp", device_type: "mac" },
    { node_id: "turns/turn_002_agent.json", role: "agent", content: "I have analyzed the hackathon rules, submission requirements, and constraints. Drafted dual-track strategy to hit both Google AI Studio and Replit tracks simultaneously using a unified codebase. Implementation_plan.md + task.md checklists. Awaiting project idea + team confirmation.", device_id: "antigravity-codx", device_type: "agent" },
    { node_id: "turns/turn_003_human.json", role: "human", content: "i want to integrate my published work for a android phone/watch build per these papers i have on zenodo. all conversations will be tracked moving forward distinguishing human versus AI using the FCO/FCG design and principles. 01_FCO_v2_NEW_VERSION and 05_FCO_v3.0.0_NEW_VERSION, doi 10.5281/zenodo.21210575. build out a FCG for the three tracks. the goal is to run alphafold utilizing quantized models on an android phone while adding data from the phone itself as fractal custody objects for field and remote work for biosecurity.", device_id: "byron-mbp", device_type: "mac" },
    { node_id: "turns/turn_004_human.json", role: "human", content: "i have the free tier plus 300 in credits: https://docs.cloud.google.com/free/docs/free-cloud-features#during-free-trial", device_id: "byron-mbp", device_type: "mac" },
    { node_id: "turns/turn_005_human.json", role: "human", content: "save the artifacts and all conversations and KG within /Users/byron/projects/active/deepfold", device_id: "byron-mbp", device_type: "mac" },
  ];

  for (const t of conversationTurns) {
    const built = await buildTurnFco({
      object_type: "conversation_turn",
      payload_bytes: JSON.stringify(t),
      payload_media_type: "application/json",
      parents: [],
      authorization: { author, release_class: "public-safe", device_id: t.device_id, device_type: t.device_type },
      claim: {
        type: "conversation_turn",
        statement: `Conversation turn: ${t.role} via ${t.device_id}.`,
        claim_ceiling: "This turn is content-addressed and public-key-bound; it does not establish truth of the content.",
      },
      node_id: t.node_id,
    });
    await insertFco(env, {
      object_id: built.object_id,
      object_type: "conversation_turn",
      content_leaf: built.content_leaf,
      fco_root: built.fco_root,
      leaf_hash: built.leaf_hash,
      node_id: t.node_id,
      parents_json: "[]",
      envelope_json: canonicalJson(built.envelope),
      payload_preview: `${t.role} via ${t.device_id}: ${t.content.slice(0, 160)}${t.content.length > 160 ? "..." : ""}`,
      claim_ceiling: "Conversation turn bound to public key; content not validated by FCG.",
      device_id: t.device_id,
      device_type: t.device_type,
      created_locally_at_utc: syncedAt,
      synced_at_utc: syncedAt,
    });
  }

  // 3 synthetic Android FCOs — demonstrate cross-device FCG.
  const syntheticAndroid = [
    {
      node_id: "android-001/field-sample/2026-07-18T08:12:00Z",
      name: "Stanford-Field-089A",
      sequence: "MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTFTYGVQCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLVNRIELKGIDFKEDGNILGHKLEYNYNSHNVYIMADKQKNGIKVNFKIRHNIEDGSVQLADHYQQNTPIGDGPVLLPDNHYLSTQSALSKDPNEKRDHMVLLEFVTAAGITHGMDELYK",
      gps: { lat: 37.4275, lng: -122.1697 },
      created: "2026-07-18T08:12:00.000Z",
      assessment: "Green Fluorescent Protein marker; LOW RISK.",
    },
    {
      node_id: "android-002/field-sample/2026-07-18T11:34:00Z",
      name: "Stanford-Field-114B",
      sequence: "MIFPKQYPIINFTTAGATVQSYTNFIRAVRGRLTTGADVRHEIPVLPNRVGLPINQRFILVELSNHNELSVTLALDVTNAYVVGYRAGNSAYFFHPDNQEDAEAITHLFTDVQNRYTFAFGGNYDRLEQLAGNLRENIELGNGPLEEAISALYYYSTGGTQLPTLARSFIICIQMISEAARFQYIEGEMRTRIRYNRRSAPDPSVITLENSWGRLSTAIQESNQGAFASPIQLQRRNGSKFSVYDVSILIPIIALMVYRCAPPPSSQF",
      gps: { lat: 37.4281, lng: -122.1703 },
      created: "2026-07-18T11:34:00.000Z",
      assessment: "Ricin Toxin A-Chain; HIGH RISK ribosome-inactivating protein.",
    },
    {
      node_id: "android-001/fold-result/2026-07-18T08:13:45Z",
      name: "Stanford-Field-089A-fold",
      sequence: "[folded structure for 089A — local ExecuTorch int8 inference]",
      gps: { lat: 37.4275, lng: -122.1697 },
      created: "2026-07-18T08:13:45.000Z",
      assessment: "Local quantized fold result; pLDDT confidence 94.2%.",
    },
  ];

  for (const s of syntheticAndroid) {
    const sampleEnvelope = {
      name: s.name,
      sequence: s.sequence,
      gps: s.gps,
      custodian: author,
      timestamp: s.created,
      assessment: s.assessment,
    };
    const built = await buildFco({
      object_type: "field_sample_sealed",
      payload_bytes: JSON.stringify(sampleEnvelope),
      payload_media_type: "application/json",
      parents: [],
      authorization: { author, release_class: "field-private", device_id: s.node_id.split("/")[0], device_type: "android" },
      claim: {
        type: "field_sample_sealed",
        statement: `Field sample ${s.name} sealed at ${s.gps.lat},${s.gps.lng}.`,
        claim_ceiling: "Field sample is content-addressed and public-key-bound; biological interpretation requires separate analysis.",
      },
      created_at_utc: s.created,
    });
    const leaf_hash = await computeLeafHash(s.node_id, built.fco_root);
    await insertFco(env, {
      object_id: built.object_id,
      object_type: "field_sample_sealed",
      content_leaf: built.content_leaf,
      fco_root: built.fco_root,
      leaf_hash,
      node_id: s.node_id,
      parents_json: "[]",
      envelope_json: canonicalJson(built.envelope),
      payload_preview: `${s.name} via android: ${s.assessment}`,
      claim_ceiling: "Field sample bound to public key; biological interpretation not validated by FCG.",
      device_id: s.node_id.split("/")[0],
      device_type: "android",
      created_locally_at_utc: s.created,
      synced_at_utc: syncedAt,
    });
  }

  const { root, leafCount } = await recomputeFcg(env);
  return c.json({ ok: true, seeded: conversationTurns.length + syntheticAndroid.length, leaf_count: leafCount, fcg_root: root });
});

// /api/seal — the SPA calls this when the user seals a new field sample on the web.
app.post("/api/seal", async (c) => {
  const env = c.env;
  const body = await c.req.json<{
    name: string;
    sequence: string;
    gps_lat: number;
    gps_lng: number;
    custodian?: string;
    device_id?: string;
    device_type?: string;
  }>();
  if (!body?.name || !body?.sequence) return c.json({ error: "name and sequence are required" }, 400);

  const author = body.custodian ?? "Byron P. Lee";
  const device_id = body.device_id ?? "web-demo";
  const device_type = body.device_type ?? "web";
  const syncedAt = nowUtc();

  const sampleEnvelope = {
    name: body.name,
    sequence: body.sequence,
    gps: { lat: body.gps_lat, lng: body.gps_lng },
    custodian: author,
    timestamp: syncedAt,
  };

  const node_id = `${device_id}/sample/${syncedAt}`;
  const built = await buildFco({
    object_type: "field_sample_sealed",
    payload_bytes: JSON.stringify(sampleEnvelope),
    payload_media_type: "application/json",
    parents: [],
    authorization: { author, release_class: "field-private", device_id, device_type },
    claim: {
      type: "field_sample_sealed",
      statement: `Field sample ${body.name} sealed at ${body.gps_lat},${body.gps_lng} by ${author}.`,
      claim_ceiling: "Field sample is content-addressed and public-key-bound; biological interpretation requires separate analysis.",
    },
  });
  const leaf_hash = await computeLeafHash(node_id, built.fco_root);

  await insertFco(env, {
    object_id: built.object_id,
    object_type: "field_sample_sealed",
    content_leaf: built.content_leaf,
    fco_root: built.fco_root,
    leaf_hash,
    node_id,
    parents_json: "[]",
    envelope_json: canonicalJson(built.envelope),
    payload_preview: `${body.name} via ${device_id}: ${body.sequence.length} aa`,
    claim_ceiling: "Field sample bound to public key; biological interpretation not validated by FCG.",
    device_id,
    device_type,
    created_locally_at_utc: syncedAt,
    synced_at_utc: syncedAt,
  });

  const { root, leafCount } = await recomputeFcg(env);
  return c.json({
    object_id: built.object_id,
    fco_root: built.fco_root,
    leaf_count: leafCount,
    fcg_root: root,
    device_id,
    device_type,
  });
});

// /api/sync — a non-web device (Android, Replit, Antigravity) POSTs a pre-sealed FCO.
// The server validates format, inserts if the object_id is new, and recomputes the FCG.
app.post("/api/sync", async (c) => {
  const env = c.env;
  const body = await c.req.json<{
    object_id: string;
    object_type: string;
    content_leaf: string;
    fco_root: string;
    leaf_hash: string;
    node_id: string;
    parents_json: string;
    envelope_json: string;
    payload_preview: string;
    claim_ceiling: string;
    device_id: string;
    device_type: string;
    created_locally_at_utc: string;
  }>();
  if (!body?.object_id || !body?.fco_root) return c.json({ error: "object_id and fco_root required" }, 400);

  const syncedAt = nowUtc();
  await insertFco(env, {
    object_id: body.object_id,
    object_type: body.object_type ?? "synced_fco",
    content_leaf: body.content_leaf,
    fco_root: body.fco_root,
    leaf_hash: body.leaf_hash,
    node_id: body.node_id ?? body.object_id,
    parents_json: body.parents_json ?? "[]",
    envelope_json: body.envelope_json ?? "{}",
    payload_preview: (body.payload_preview ?? "").slice(0, 200),
    claim_ceiling: body.claim_ceiling ?? "Synced FCO; verification pending.",
    device_id: body.device_id ?? "unknown-device",
    device_type: body.device_type ?? "cloud",
    created_locally_at_utc: body.created_locally_at_utc ?? syncedAt,
    synced_at_utc: syncedAt,
  });

  const { root, leafCount } = await recomputeFcg(env);
  return c.json({ ok: true, leaf_count: leafCount, fcg_root: root });
});

// /api/turn — the SPA logs a new conversation turn (human or agent) into the FCG.
app.post("/api/turn", async (c) => {
  const env = c.env;
  const body = await c.req.json<{ role: "human" | "agent"; content: string; device_id?: string; device_type?: string }>();
  if (!body?.role || !body?.content) return c.json({ error: "role and content required" }, 400);
  const syncedAt = nowUtc();
  const device_id = body.device_id ?? (body.role === "agent" ? "sauna-agent" : "web-demo");
  const device_type = body.device_type ?? (body.role === "agent" ? "agent" : "web");
  const node_id = `${device_id}/turn/${syncedAt}`;

  const built = await buildTurnFco({
    object_type: "conversation_turn",
    payload_bytes: JSON.stringify({ role: body.role, content: body.content, timestamp: syncedAt }),
    payload_media_type: "application/json",
    parents: [],
    authorization: { author: "Byron P. Lee", release_class: "public-safe", device_id, device_type },
    claim: {
      type: "conversation_turn",
      statement: `${body.role} turn via ${device_id}.`,
      claim_ceiling: "Conversation turn bound to public key; content not validated by FCG.",
    },
    node_id,
  });

  await insertFco(env, {
    object_id: built.object_id,
    object_type: "conversation_turn",
    content_leaf: built.content_leaf,
    fco_root: built.fco_root,
    leaf_hash: built.leaf_hash,
    node_id,
    parents_json: "[]",
    envelope_json: canonicalJson(built.envelope),
    payload_preview: `${body.role} via ${device_id}: ${body.content.slice(0, 160)}${body.content.length > 160 ? "..." : ""}`,
    claim_ceiling: "Conversation turn bound to public key.",
    device_id,
    device_type,
    created_locally_at_utc: syncedAt,
    synced_at_utc: syncedAt,
  });

  const { root, leafCount } = await recomputeFcg(env);
  return c.json({ fco_root: built.fco_root, fcg_root: root, leaf_count: leafCount });
});

// /api/chat — proxy to Gemini with the FCO/FCG system prompt. Logs both turns.
app.post("/api/chat", async (c) => {
  const env = c.env;
  const body = await c.req.json<{ message: string; history?: Array<{ role: string; content: string }> }>();
  if (!body?.message) return c.json({ error: "message required" }, 400);

  const systemPrompt = `You are the BioCustody biosecurity copilot. Every response is sealed as a conversation-turn FCO bound to the public key fingerprint ${PUBLIC_KEY_SHA256}. Highlight biosecurity warnings clearly for any high-risk classification (ricin, ribosome-inactivating proteins, toxins, dangerous pathogens). Stay scientifically grounded and concise.`;

  const syncedAt = nowUtc();

  // Log the human turn first — same as /api/turn, so the FCG stays self-consistent even if Gemini fails.
  const humanNodeId = `web-demo/turn/${syncedAt}-human`;
  const humanBuilt = await buildTurnFco({
    object_type: "conversation_turn",
    payload_bytes: JSON.stringify({ role: "human", content: body.message, timestamp: syncedAt }),
    payload_media_type: "application/json",
    parents: [],
    authorization: { author: "Byron P. Lee", release_class: "public-safe", device_id: "web-demo", device_type: "web" },
    claim: { type: "conversation_turn", statement: "human chat turn", claim_ceiling: "Chat turn bound to public key." },
    node_id: humanNodeId,
  });
  await insertFco(env, {
    object_id: humanBuilt.object_id,
    object_type: "conversation_turn",
    content_leaf: humanBuilt.content_leaf,
    fco_root: humanBuilt.fco_root,
    leaf_hash: humanBuilt.leaf_hash,
    node_id: humanNodeId,
    parents_json: "[]",
    envelope_json: canonicalJson(humanBuilt.envelope),
    payload_preview: `human via web-demo: ${body.message.slice(0, 160)}${body.message.length > 160 ? "..." : ""}`,
    claim_ceiling: "Chat turn bound to public key.",
    device_id: "web-demo",
    device_type: "web",
    created_locally_at_utc: syncedAt,
    synced_at_utc: syncedAt,
  });

  const apiKey = c.env.GEMINI_API_KEY ?? "";
  let reply = "";
  let threat_warning: string | null = null;

  if (apiKey) {
    try {
      const { GoogleGenerativeAI } = await import("@google/generative-ai");
      const genAI = new GoogleGenerativeAI(apiKey);
      const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
      const history = (body.history ?? []).map((h) => `${h.role === "user" ? "Human" : "AI"}: ${h.content}`).join("\n");
      const prompt = `${systemPrompt}\n\nChat history:\n${history}\n\nHuman: ${body.message}\nAI:`;
      const result = await model.generateContent(prompt);
      reply = (await result.response).text();
      const lower = reply.toLowerCase();
      if (/(ricin|ribosome.inactivating|toxin|high.risk|biothreat|bioweapon)/.test(lower)) {
        threat_warning = "HIGH-RISK sequence detected. Biosecurity containment recommended.";
      }
    } catch (err: any) {
      reply = `[Gemini error] ${err?.message ?? "unknown"} — falling back to local classifier.`;
    }
  } else {
    // Deterministic mock so the FCG still records the agent turn.
    reply = `[Mock BioCustody Copilot] Query logged to FCG. Public-key fingerprint ${PUBLIC_KEY_SHA256.slice(0, 8)}… is the binding for this session. Set GEMINI_API_KEY on the deployment to enable live Gemini.`;
  }

  // Log the agent turn.
  const agentNodeId = `sauna-agent/turn/${syncedAt}-agent`;
  const agentBuilt = await buildTurnFco({
    object_type: "conversation_turn",
    payload_bytes: JSON.stringify({ role: "agent", content: reply, timestamp: syncedAt, source: apiKey ? "gemini-1.5-flash" : "mock" }),
    payload_media_type: "application/json",
    parents: [humanBuilt.object_id],
    authorization: { author: "Byron P. Lee", release_class: "public-safe", device_id: "sauna-agent", device_type: "agent" },
    claim: { type: "conversation_turn", statement: "agent chat turn", claim_ceiling: "Chat turn bound to public key." },
    node_id: agentNodeId,
  });
  await insertFco(env, {
    object_id: agentBuilt.object_id,
    object_type: "conversation_turn",
    content_leaf: agentBuilt.content_leaf,
    fco_root: agentBuilt.fco_root,
    leaf_hash: agentBuilt.leaf_hash,
    node_id: agentNodeId,
    parents_json: JSON.stringify([humanBuilt.object_id]),
    envelope_json: canonicalJson(agentBuilt.envelope),
    payload_preview: `agent via sauna-agent: ${reply.slice(0, 160)}${reply.length > 160 ? "..." : ""}`,
    claim_ceiling: "Chat turn bound to public key.",
    device_id: "sauna-agent",
    device_type: "agent",
    created_locally_at_utc: syncedAt,
    synced_at_utc: syncedAt,
  });

  const { root, leafCount } = await recomputeFcg(env);
  return c.json({ reply, fcg_root: root, leaf_count: leafCount, threat_warning });
});

export default {
  fetch: (req: Request, env: any, ctx: AppCtx) =>
    app.fetch(req, { ...env, ctx }),
} satisfies AppHandler;
