CREATE TABLE `fcg_state` (
	`id` integer PRIMARY KEY NOT NULL,
	`merkle_root` text NOT NULL,
	`leaf_count` integer NOT NULL,
	`updated_at_utc` text NOT NULL
);

--> statement-breakpoint
CREATE TABLE `fcos` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`object_id` text NOT NULL,
	`object_type` text NOT NULL,
	`content_leaf` text NOT NULL,
	`fco_root` text NOT NULL,
	`leaf_hash` text NOT NULL,
	`node_id` text NOT NULL,
	`parents_json` text NOT NULL,
	`envelope_json` text NOT NULL,
	`payload_preview` text NOT NULL,
	`claim_ceiling` text NOT NULL,
	`device_id` text NOT NULL,
	`device_type` text NOT NULL,
	`created_locally_at_utc` text NOT NULL,
	`synced_at_utc` text NOT NULL
);

--> statement-breakpoint
CREATE UNIQUE INDEX `fcos_object_id_unique` ON `fcos` (`object_id`);
--> statement-breakpoint
CREATE INDEX `fcos_created_idx` ON `fcos` (`created_locally_at_utc`);
--> statement-breakpoint
CREATE INDEX `fcos_device_idx` ON `fcos` (`device_id`);
