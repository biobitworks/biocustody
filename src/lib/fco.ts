// FCO v3 primitives — distinct from voiceworks' RFC-6962 build.
// - File FCO root: sha256(0x00 || file_sha256 || 0x00 || public_key_sha256)
// - Conversation turn leaf: sha256(0x00 || utf8(node_id || "|" || fco_root))
// - Graph root: Merkle Mountain Range (MMR), bagged right-to-left, parent prefix 0x01
//
// All hashes via Web Crypto so it works in both the handler and the browser.
// Byron P. Lee / 903fec78

export const PUBLIC_KEY_SHA256 =
  "903fec780c8219cccec286d845d3f58da70fa3b2969a8ad4a77bfc58fa1a8c35";

const enc = new TextEncoder();

function toHex(buf: ArrayBuffer | Uint8Array): string {
  const b = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let out = "";
  for (let i = 0; i < b.length; i++) out += b[i].toString(16).padStart(2, "0");
  return out;
}

export async function sha256Hex(bytes: Uint8Array | string): Promise<string> {
  const data = typeof bytes === "string" ? enc.encode(bytes) : bytes;
  const buf = new ArrayBuffer(data.length);
  new Uint8Array(buf).set(data);
  const digest = await crypto.subtle.digest("SHA-256", buf);
  return toHex(digest);
}

// File FCO root: sha256(0x00 || file_sha256_hex || 0x00 || public_key_sha256_hex)
export async function computeFcoRoot(
  fileSha256Hex: string,
  publicKeySha256: string = PUBLIC_KEY_SHA256,
): Promise<string> {
  const fileBytes = enc.encode(fileSha256Hex);
  const keyBytes = enc.encode(publicKeySha256);
  const concat = new Uint8Array(1 + fileBytes.length + 1 + keyBytes.length);
  concat[0] = 0x00;
  concat.set(fileBytes, 1);
  concat[1 + fileBytes.length] = 0x00;
  concat.set(keyBytes, 1 + fileBytes.length + 1);
  return sha256Hex(concat);
}

// Conversation turn leaf hash: sha256(0x00 || utf8(node_id || "|" || fco_root))
export async function computeLeafHash(
  nodeId: string,
  fcoRoot: string,
): Promise<string> {
  const data = enc.encode(`${nodeId}|${fcoRoot}`);
  const concat = new Uint8Array(1 + data.length);
  concat[0] = 0x00;
  concat.set(data, 1);
  return sha256Hex(concat);
}

// Parent node hash: sha256(0x01 || left_hex || right_hex)
async function merkleParent(leftHex: string, rightHex: string): Promise<string> {
  const l = enc.encode(leftHex);
  const r = enc.encode(rightHex);
  const concat = new Uint8Array(1 + l.length + r.length);
  concat[0] = 0x01;
  concat.set(l, 1);
  concat.set(r, 1 + l.length);
  return sha256Hex(concat);
}

// Merkle Mountain Range — bagged right-to-left, deterministic.
export async function mmr(leaves: string[]): Promise<string> {
  if (leaves.length === 0) {
    return "0000000000000000000000000000000000000000000000000000000000000000";
  }
  if (leaves.length === 1) return leaves[0];

  type Peak = { height: number; root: string };
  const stack: Peak[] = [];
  for (const leaf of leaves) {
    let height = 0;
    let root = leaf;
    while (stack.length > 0 && stack[stack.length - 1].height === height) {
      const left = stack.pop()!.root;
      root = await merkleParent(left, root);
      height += 1;
    }
    stack.push({ height, root });
  }
  // Bag right-to-left: combine peaks from the rightmost inward.
  let bagged = stack[stack.length - 1].root;
  for (let i = stack.length - 2; i >= 0; i--) {
    bagged = await merkleParent(stack[i].root, bagged);
  }
  return bagged;
}

// Canonical JSON for content hashing (stable key order, no whitespace).
export function canonicalJson(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(canonicalJson).join(",") + "]";
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  const parts = keys.map((k) => JSON.stringify(k) + ":" + canonicalJson(obj[k]));
  return "{" + parts.join(",") + "}";
}

export interface FcoEnvelope {
  fco_version: "v3";
  object_type: string;
  parents: string[];
  payload: { media_type: string; bytes_sha256: string; byte_length: number };
  authorization: { author: string; release_class: string; device_id?: string; device_type?: string };
  claim: { type: string; statement: string; claim_ceiling: string };
  created_at_utc: string;
}

export interface BuildFcoOpts {
  object_type: string;
  payload_bytes: Uint8Array | string;
  payload_media_type: string;
  parents: string[];
  authorization: { author: string; release_class: string; device_id?: string; device_type?: string };
  claim: { type: string; statement: string; claim_ceiling: string };
  created_at_utc?: string;
  public_key_sha256?: string;
}

export interface BuiltFco {
  envelope: FcoEnvelope;
  object_id: string;
  content_leaf: string;
  fco_root: string;
  leaf_hash: string;
}

export async function buildFco(opts: BuildFcoOpts): Promise<BuiltFco> {
  const data = typeof opts.payload_bytes === "string"
    ? enc.encode(opts.payload_bytes)
    : opts.payload_bytes;
  const bytes_sha256 = await sha256Hex(data);
  const created_at_utc = opts.created_at_utc ?? new Date().toISOString();

  const envelope: FcoEnvelope = {
    fco_version: "v3",
    object_type: opts.object_type,
    parents: opts.parents,
    payload: {
      media_type: opts.payload_media_type,
      bytes_sha256,
      byte_length: data.length,
    },
    authorization: opts.authorization,
    claim: opts.claim,
    created_at_utc,
  };

  const canonical = canonicalJson(envelope);
  const content_leaf = await sha256Hex(enc.encode(canonical));
  const fco_root = await computeFcoRoot(content_leaf, opts.public_key_sha256);
  const object_id = `sha256:${content_leaf}`;
  // For non-turn objects, leaf_hash defaults to fco_root (no conversation-node form).
  const leaf_hash = fco_root;

  return { envelope, object_id, content_leaf, fco_root, leaf_hash };
}

// Helper for conversation turns: builds the FCO and the conversation-leaf hash together.
export async function buildTurnFco(opts: BuildFcoOpts & { node_id: string }): Promise<BuiltFco & { node_id: string }> {
  const built = await buildFco(opts);
  const leaf_hash = await computeLeafHash(opts.node_id, built.fco_root);
  return { ...built, leaf_hash, node_id: opts.node_id };
}
