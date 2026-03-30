# AEGIS Phase 2 Database Design (Detailed)

This document defines the persistence schema for gateway-local SQLite storage.

## Design goals
- Preserve **enforcement-before-persistence** for measurement ingestion.
- Keep observability read-heavy queries fast via targeted indexes.
- Keep verification/admin audit streams tamper-evident using append-only hash-linking.
- Ensure rejected packets are isolated from verification/Merkle aggregation paths.

---

## 1) `users`
### Purpose
Local gateway accounts used for authentication and authorization.

### Fields
- `id` TEXT(36) UUID, PK
- `username` TEXT(64), unique
- `password_hash` TEXT(255)
- `role` ENUM(`viewer`, `operator`)
- `is_active` BOOLEAN
- `created_at` DATETIME (UTC)
- `updated_at` DATETIME (UTC)

### Keys & indexes
- PK: `id`
- Unique: `username`
- Indexes: `username`, `role`

### Constraints
- `username` unique
- `role` must be valid enum

### Immutable fields
- `id`, `created_at`

### Query-optimized fields
- `username`, `role`, `is_active`

---

## 2) `enrollment_registry`
### Purpose
Registry of allowed nodes and enrollment metadata.

### Fields
- `id` TEXT(36) UUID, PK
- `node_id` TEXT(128), unique
- `display_name` TEXT(128)
- `pubkey_fingerprint` TEXT(128), nullable
- `enrolled_by_user_id` TEXT(36), FK -> `users.id`
- `enrollment_status` ENUM(`active`, `revoked`)
- `created_at` DATETIME (UTC)
- `revoked_at` DATETIME nullable

### Keys & indexes
- PK: `id`
- FK: `enrolled_by_user_id -> users.id`
- Unique: `node_id`
- Indexes: `node_id`, `enrolled_by_user_id`, `enrollment_status`

### Constraints
- enum value for `enrollment_status`

### Immutable fields
- `id`, `node_id`, `created_at`, `enrolled_by_user_id`

### Query-optimized fields
- `node_id`, `enrollment_status`

---

## 3) `session_state`
### Purpose
Tracks current enforcement session context for ingestion consistency.

### Fields
- `id` INTEGER PK (singleton = 1)
- `current_session_id` TEXT(36)
- `session_started_at` DATETIME (UTC)
- `reset_counter` INTEGER
- `updated_at` DATETIME (UTC)

### Keys & indexes
- PK: `id`
- Index: `current_session_id`

### Constraints
- Check: `id = 1`

### Immutable fields
- `id`

### Query-optimized fields
- `current_session_id`

---

## 4) `verification_log` (append-only, hash-linked)
### Purpose
Accepted measurements after enforcement.

### Fields
- `id` INTEGER PK autoincrement
- `session_id` TEXT(36)
- `node_id` TEXT(128)
- `gateway_received_at` DATETIME (UTC)
- `device_timestamp` DATETIME (UTC)
- `payload_canonical_json` TEXT
- `payload_hash` TEXT(64)
- `validation_profile_version` TEXT(32)
- `prev_hash` TEXT(64), nullable (genesis)
- `curr_hash` TEXT(64), unique

### Keys & indexes
- PK: `id`
- Unique: `curr_hash`
- Indexes: `session_id`, `node_id`, `gateway_received_at`, `curr_hash`
- Composite index (optimization): `(session_id, id)`

### Constraints
- `curr_hash` unique
- append-only triggers prevent UPDATE/DELETE

### Immutable fields
- all columns (after INSERT)

### Hash-link fields
- `id`, `session_id`, `node_id`, `gateway_received_at`, `payload_hash`, `prev_hash`

### Query-optimized fields
- `session_id`, `node_id`, `gateway_received_at`, `id`

---

## 5) `rejection_log` (append-only, separate stream)
### Purpose
Rejected measurements and reasons, excluded from Merkle.

### Fields
- `id` INTEGER PK autoincrement
- `session_id` TEXT(36)
- `node_id` TEXT(128)
- `gateway_received_at` DATETIME (UTC)
- `device_timestamp` DATETIME nullable
- `payload_canonical_json` TEXT
- `rejection_code` TEXT(64)
- `rejection_reason` TEXT
- `rule_version` TEXT(32)

### Keys & indexes
- PK: `id`
- Indexes: `session_id`, `node_id`, `gateway_received_at`, `rejection_code`
- Composite index (optimization): `(session_id, rejection_code, id)`

### Constraints
- Check: `rejection_code <> ''`
- append-only triggers prevent UPDATE/DELETE

### Immutable fields
- all columns (after INSERT)

### Hash-link fields
- none (separate non-Merkle stream)

### Query-optimized fields
- `session_id`, `rejection_code`, `node_id`, `gateway_received_at`

---

## 6) `merkle_batches`
### Purpose
Stores batched ranges of accepted verification records.

### Fields
- `id` INTEGER PK autoincrement
- `batch_uuid` TEXT(36), unique
- `session_id` TEXT(36)
- `from_verification_id` INTEGER
- `to_verification_id` INTEGER
- `leaf_count` INTEGER
- `merkle_root` TEXT(64)
- `created_at` DATETIME (UTC)
- `status` ENUM(`pending`, `anchored`, `failed`)

### Keys & indexes
- PK: `id`
- Unique: `batch_uuid`
- Indexes: `session_id`, `merkle_root`, `status`

### Constraints
- `leaf_count > 0`
- `to_verification_id >= from_verification_id`

### Immutable fields
- batch range and root fields should be immutable after insert; only `status` may evolve

### Hash-link fields
- not hash-linked row-by-row; references hash-linked verification leaves

### Query-optimized fields
- `status`, `created_at`, `session_id`

---

## 7) `blockchain_anchors`
### Purpose
Anchor transaction outcomes for Merkle roots.

### Fields
- `id` INTEGER PK autoincrement
- `merkle_batch_id` INTEGER FK -> `merkle_batches.id`, unique
- `chain` TEXT(32)
- `tx_signature` TEXT(128), nullable
- `slot` INTEGER nullable
- `anchored_at` DATETIME nullable
- `confirm_status` ENUM(`pending`, `confirmed`, `failed`)
- `error_message` TEXT nullable

### Keys & indexes
- PK: `id`
- FK: `merkle_batch_id -> merkle_batches.id`
- Unique: `merkle_batch_id`
- Indexes: `tx_signature`, `confirm_status`

### Constraints
- enum values for `confirm_status`

### Immutable fields
- `id`, `merkle_batch_id`, `chain`; status fields may update with confirmations

### Query-optimized fields
- `confirm_status`, `tx_signature`

---

## 8) `admin_action_log` (append-only, hash-linked)
### Purpose
Tamper-evident audit of privileged/admin actions.

### Fields
- `id` INTEGER PK autoincrement
- `occurred_at` DATETIME (UTC)
- `actor_user_id` TEXT(36), FK -> `users.id`
- `action_type` ENUM(`node_enroll`, `node_revoke`, `session_reset`, `export_request`, `user_login`)
- `target_type` TEXT(64)
- `target_id` TEXT(64)
- `request_id` TEXT(64), nullable
- `action_payload_json` TEXT
- `prev_hash` TEXT(64), nullable
- `curr_hash` TEXT(64), unique

### Keys & indexes
- PK: `id`
- FK: `actor_user_id -> users.id`
- Unique: `curr_hash`
- Indexes: `occurred_at`, `actor_user_id`, `action_type`, `curr_hash`
- Composite index (optimization): `(action_type, occurred_at)`

### Constraints
- append-only triggers prevent UPDATE/DELETE

### Immutable fields
- all columns (after INSERT)

### Hash-link fields
- `actor_user_id`, `action_type`, `target_type`, `target_id`, `action_payload_json`, `request_id`, `prev_hash`

### Query-optimized fields
- `occurred_at`, `actor_user_id`, `action_type`

---

## 9) `audit_exports`
### Purpose
Tracks export requests and output artifacts for audits.

### Fields
- `id` INTEGER PK autoincrement
- `requested_at` DATETIME (UTC)
- `requested_by_user_id` TEXT(36), FK -> `users.id`
- `export_type` TEXT(64)
- `filter_json` TEXT
- `status` ENUM(`queued`, `completed`, `failed`)
- `artifact_path` TEXT(255), nullable
- `artifact_hash` TEXT(64), nullable
- `completed_at` DATETIME nullable

### Keys & indexes
- PK: `id`
- FK: `requested_by_user_id -> users.id`
- Indexes: `requested_at`, `requested_by_user_id`, `status`

### Immutable fields
- `id`, `requested_at`, `requested_by_user_id`, request params

### Query-optimized fields
- `status`, `requested_at`, `requested_by_user_id`

---

## Append-only strategy
- DB-level triggers disallow UPDATE/DELETE on:
  - `verification_log`
  - `rejection_log`
  - `admin_action_log`
- API/service layers expose insert/list/read operations only for those tables.

## `prev_hash` and `curr_hash` computation
1. Fetch previous row hash (`prev_hash`) from same stream ordered by `id` DESC.
2. Build canonical payload with stable key order + normalized datetime.
3. Compute `curr_hash = SHA256(canonical_json(payload_without_curr_hash))`.
4. Insert new row with both hashes.

## Rejected record separation
- Enforcement failures go to `rejection_log` only.
- Merkle batching reads exclusively from `verification_log` id ranges.
- No Merkle references are built from `rejection_log` rows.

## Admin actions in same tamper-evident model
- `admin_action_log` uses the same hash-chain strategy as verification records.
- Privileged commands (enroll/reset/export/etc.) append an immutable, hash-linked row.
- Phase 4 routes commit domain mutation + audit append atomically.

## Alembic migration files
- `20260330_0001_initial_phase2_schema.py`: base tables, enums, indexes, FKs.
- `20260330_0002_append_only_guards.py`: append-only triggers and additional composite indexes.
