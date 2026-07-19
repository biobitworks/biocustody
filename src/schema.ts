import { sqliteTable, integer, text, index } from "drizzle-orm/sqlite-core";

// One row per FCO node. The custody graph lives here.
// device_id + device_type make this cross-device: a single FCG spans web, android, replit, cloud, agent.
export const fcos = sqliteTable("fcos", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  object_id: text("object_id").notNull().unique(),         // sha256:<content-leaf-hex>
  object_type: text("object_type").notNull(),              // sample | turn | page_view | sync_import | mock_chat | etc.
  content_leaf: text("content_leaf").notNull(),
  fco_root: text("fco_root").notNull(),                     // public-key-bound FCO root
  leaf_hash: text("leaf_hash").notNull(),                   // graph leaf (for turns: f(node_id|fco_root))
  node_id: text("node_id").notNull(),                      // stable id used as MMR leaf key
  parents_json: text("parents_json").notNull(),            // JSON array of object_ids
  envelope_json: text("envelope_json").notNull(),          // full canonical FCO envelope
  payload_preview: text("payload_preview").notNull(),       // first ~200 chars for display
  claim_ceiling: text("claim_ceiling").notNull(),
  device_id: text("device_id").notNull(),                  // web-demo | android-001 | replit-prod | sauna-agent | etc.
  device_type: text("device_type").notNull(),              // web | android | replit | cloud | agent
  created_locally_at_utc: text("created_locally_at_utc").notNull(),
  synced_at_utc: text("synced_at_utc").notNull(),
}, (t) => ({
  byCreatedAt: index("fcos_created_idx").on(t.created_locally_at_utc),
  byDevice: index("fcos_device_idx").on(t.device_id),
}));

// Singleton app-state row: the last computed FCG root + leaf count, cached for /api/live.
export const fcgState = sqliteTable("fcg_state", {
  id: integer("id").primaryKey(),                          // always 1
  merkle_root: text("merkle_root").notNull(),
  leaf_count: integer("leaf_count").notNull(),
  updated_at_utc: text("updated_at_utc").notNull(),
});
