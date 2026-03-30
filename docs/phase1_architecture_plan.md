# AEGIS Website + Database Architecture Plan (Phase 1)

## A) Architecture Overview

AEGIS is split into isolated modules with strict write boundaries:

1. **MQTT Ingestion Service**
   - Subscribes to Mosquitto topics.
   - Converts MQTT payloads into internal packet DTOs.
   - Hands packets to enforcement engine only.
   - No direct DB writes from UI/API paths.

2. **Enforcement Engine**
   - Performs acquisition-time checks (timestamp freshness, session rules, sequence checks, schema checks).
   - Emits one of two events:
     - `PacketAccepted` for verification log append.
     - `PacketRejected` for rejection log append.
   - Immutable decision output.

3. **Persistence Layer**
   - Appends accepted packets to `verification_log` (hash-linked).
   - Appends rejected packets to `rejection_log` (separate stream).
   - Appends operator activity to `admin_action_log` (hash-linked).
   - Maintains session and registry state.

4. **Merkle + Anchoring Service**
   - Periodically batches only accepted verification records.
   - Builds Merkle root.
   - Writes `merkle_batches`.
   - Asynchronously anchors root to Solana Devnet and writes `blockchain_anchors`.
   - Never blocks ingestion path.

5. **API Backend (FastAPI)**
   - Read-mostly observability API for UI.
   - Authenticated operator API for controlled admin actions.
   - Writes admin commands only through service layer; never writes measurement records directly.

6. **Frontend UI (React)**
   - Operator console + observability dashboard.
   - Uses API only.
   - No broker access; no direct DB access.

## B) Proposed Folder Structure

```text
Thesisv4/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── v1_router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── workers/
│   │   └── main.py
│   ├── alembic/
│   │   └── versions/
│   ├── tests/
│   ├── pyproject.toml
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── pages/
│   │   ├── services/
│   │   └── main.tsx
│   └── package.json
└── docs/
    └── phase1_architecture_plan.md
```

## C) Database Schema Proposal

### 1. `users`
- Purpose: local operator/viewer accounts.
- Fields:
  - `id` (TEXT UUID, PK)
  - `username` (TEXT, unique, indexed)
  - `password_hash` (TEXT)
  - `role` (TEXT: `viewer` or `operator`, indexed)
  - `is_active` (BOOLEAN)
  - `created_at` (DATETIME)
  - `updated_at` (DATETIME)
- Mutable: `password_hash`, `is_active`, `updated_at`.

### 2. `enrollment_registry`
- Purpose: enrolled IoT nodes + metadata.
- Fields:
  - `id` (TEXT UUID, PK)
  - `node_id` (TEXT, unique, indexed)
  - `display_name` (TEXT)
  - `pubkey_fingerprint` (TEXT, nullable)
  - `enrolled_by_user_id` (FK users.id)
  - `enrollment_status` (TEXT: active/revoked)
  - `created_at` (DATETIME)
  - `revoked_at` (DATETIME nullable)
- Immutable: `node_id`, `created_at`, `enrolled_by_user_id`.

### 3. `session_state`
- Purpose: current enforcement session metadata.
- Fields:
  - `id` (INTEGER PK, fixed singleton row = 1)
  - `current_session_id` (TEXT UUID, indexed)
  - `session_started_at` (DATETIME)
  - `reset_counter` (INTEGER)
  - `updated_at` (DATETIME)

### 4. `verification_log` (append-only)
- Purpose: accepted packets.
- Fields:
  - `id` (INTEGER PK autoincrement)
  - `session_id` (TEXT, indexed)
  - `node_id` (TEXT, indexed)
  - `gateway_received_at` (DATETIME, indexed)
  - `device_timestamp` (DATETIME)
  - `payload_canonical_json` (TEXT)
  - `payload_hash` (TEXT)
  - `validation_profile_version` (TEXT)
  - `prev_hash` (TEXT)
  - `curr_hash` (TEXT, unique, indexed)
- Immutable: all fields after insert.
- Hash-link fields: `id`, `session_id`, `node_id`, `gateway_received_at`, `payload_hash`, `prev_hash`.

### 5. `rejection_log` (append-only, separate)
- Purpose: rejected packets and reasons.
- Fields:
  - `id` (INTEGER PK autoincrement)
  - `session_id` (TEXT, indexed)
  - `node_id` (TEXT, indexed)
  - `gateway_received_at` (DATETIME, indexed)
  - `device_timestamp` (DATETIME nullable)
  - `payload_canonical_json` (TEXT)
  - `rejection_code` (TEXT, indexed)
  - `rejection_reason` (TEXT)
  - `rule_version` (TEXT)
- Explicitly excluded from Merkle batches.

### 6. `merkle_batches`
- Purpose: snapshots of accepted log ranges.
- Fields:
  - `id` (INTEGER PK)
  - `batch_uuid` (TEXT UUID unique)
  - `session_id` (TEXT, indexed)
  - `from_verification_id` (INTEGER)
  - `to_verification_id` (INTEGER)
  - `leaf_count` (INTEGER)
  - `merkle_root` (TEXT, indexed)
  - `created_at` (DATETIME)
  - `status` (TEXT: pending/anchored/failed, indexed)
- Constraint: `leaf_count > 0`.

### 7. `blockchain_anchors`
- Purpose: on-chain anchoring outcomes.
- Fields:
  - `id` (INTEGER PK)
  - `merkle_batch_id` (FK merkle_batches.id, unique)
  - `chain` (TEXT, default `solana-devnet`)
  - `tx_signature` (TEXT, indexed)
  - `slot` (INTEGER nullable)
  - `anchored_at` (DATETIME nullable)
  - `confirm_status` (TEXT indexed)
  - `error_message` (TEXT nullable)

### 8. `admin_action_log` (append-only hash-linked)
- Purpose: tamper-evident log of privileged actions.
- Fields:
  - `id` (INTEGER PK autoincrement)
  - `occurred_at` (DATETIME, indexed)
  - `actor_user_id` (FK users.id, indexed)
  - `action_type` (TEXT, indexed)
  - `target_type` (TEXT)
  - `target_id` (TEXT)
  - `request_id` (TEXT)
  - `action_payload_json` (TEXT)
  - `prev_hash` (TEXT)
  - `curr_hash` (TEXT unique, indexed)
- Immutable after insert.

### 9. `audit_exports`
- Purpose: export requests and output artifacts.
- Fields:
  - `id` (INTEGER PK)
  - `requested_at` (DATETIME, indexed)
  - `requested_by_user_id` (FK users.id, indexed)
  - `export_type` (TEXT)
  - `filter_json` (TEXT)
  - `status` (TEXT indexed)
  - `artifact_path` (TEXT nullable)
  - `artifact_hash` (TEXT nullable)
  - `completed_at` (DATETIME nullable)

### Append-only + Hash-link strategy
- `verification_log` and `admin_action_log` are never updated/deleted.
- `prev_hash` = `curr_hash` of prior row in same stream (`NULL` for genesis).
- `curr_hash` = `SHA256(canonical_serialization_of_record_without_curr_hash)`.
- Canonical serialization: sorted JSON keys, stable timestamps (UTC ISO-8601), fixed field order.
- DB-level protection: no API update/delete endpoints; service-level guard rails; optional triggers in later migration.

### Rejected record separation
- Rejections stored only in `rejection_log`.
- Merkle worker queries only `verification_log` id range.
- Foreign keys from `merkle_batches` refer to verification IDs only.

## D) Implementation Roadmap

1. **Phase 1 (current)**: backend scaffold + settings + DB session + health endpoints + Alembic wiring.
2. **Phase 2**: SQLAlchemy models + first Alembic migration for full schema.
3. **Phase 3**: auth + RBAC + admin action logging service.
4. **Phase 4**: node enrollment/session reset APIs.
5. **Phase 5**: observability read APIs (verification/rejection/merkle/anchor/dashboard).
6. **Phase 6**: export/proof APIs + artifact generation.
7. **Phase 7**: frontend scaffold + auth shell + dashboard.
8. **Phase 8**: frontend observability/admin pages.
9. **Phase 9**: background workers (merkle + anchor async) and integration hardening.
10. **Phase 10**: test suite expansion + Raspberry Pi deployment scripts.
