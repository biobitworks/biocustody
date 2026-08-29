import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import Ajv2020 from "ajv/dist/2020.js";
import canonicalize from "canonicalize";

function canonicalHashV2(payload) {
  const bytes = canonicalize(payload);
  return createHash("sha256").update(bytes).digest("hex");
}

test("JSON property reorder → same semantic hash (Node canonicalize)", () => {
  const a = { domain: "test", schema_version: "1", semantic_payload: { z: 1, a: 2 } };
  const b = { domain: "test", schema_version: "1", semantic_payload: { a: 2, z: 1 } };
  assert.equal(canonicalHashV2(a), canonicalHashV2(b));
});

test("author permutation → different citation semantic envelope hash", () => {
  const envA = {
    domain: "fco.citation.v2",
    schema_version: "1.0.0",
    semantic_payload: {
      authors_ordered: ["Smith, J.", "Doe, A."],
      title: "Title",
      year: 2020,
      doi: "",
    },
  };
  const envB = {
    ...envA,
    semantic_payload: {
      ...envA.semantic_payload,
      authors_ordered: ["Doe, A.", "Smith, J."],
    },
  };
  assert.notEqual(canonicalHashV2(envA), canonicalHashV2(envB));
});

test("source_occurrence schema validates minimal object", () => {
  const ajv = new Ajv2020({ strict: false });
  const schema = JSON.parse(
    readFileSync(new URL("../../schemas/fcg_core/source_occurrence.schema.json", import.meta.url))
  );
  const validate = ajv.compile(schema);
  const ok = validate({
    schema_version: "1.0.0",
    provider: "LOCAL_FILE",
    content_id: "a".repeat(64),
    occurrence_id: "b".repeat(64),
    source_locator: "file:///tmp/x",
    acquired_bytes_sha256: "a".repeat(64),
  });
  assert.equal(ok, true);
});
