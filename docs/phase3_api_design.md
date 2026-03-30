# AEGIS Phase 3 API Design (REST Contract)

This phase defines the API contract for the gateway web UI and operator workflows.

## Global API conventions
- Base path: `/api/v1`
- Content type: `application/json`
- Time format: ISO-8601 UTC strings
- Auth mechanism: Bearer JWT in `Authorization: Bearer <token>`
- Roles:
  - `viewer`: read-only observability
  - `operator`: observability + privileged actions (enroll/reset/export)
- Pagination defaults: `limit=100`, `offset=0`, max `limit=500`

## Standard error envelope
```json
{
  "detail": "human readable message"
}
```

---

## 1) Operator Authentication

### 1.1 Bootstrap first operator
- **Method**: `POST`
- **Route**: `/api/v1/auth/bootstrap`
- **Request schema**:
  - `username: string (3..64)`
  - `password: string (8..128)`
- **Response schema**:
  - `id: string`
  - `username: string`
  - `role: "operator"|"viewer"`
  - `is_active: boolean`
- **Auth requirement**: none (allowed only when no user exists)
- **Validation rules**:
  - username length and uniqueness
  - bootstrap forbidden if user count > 0
- **Error responses**:
  - `400` bootstrap disabled / invalid payload

### 1.2 Login
- **Method**: `POST`
- **Route**: `/api/v1/auth/login`
- **Request schema**:
  - `username: string`
  - `password: string`
- **Response schema**:
  - `access_token: string`
  - `token_type: "bearer"`
- **Auth requirement**: none
- **Validation rules**:
  - credentials must match active user
- **Error responses**:
  - `401` invalid credentials / inactive user

### 1.3 Current identity
- **Method**: `GET`
- **Route**: `/api/v1/auth/me`
- **Request schema**: none
- **Response schema**:
  - `id, username, role, is_active`
- **Auth requirement**: authenticated (`viewer` or `operator`)
- **Validation rules**:
  - valid, non-expired JWT
- **Error responses**:
  - `401` invalid/expired token

---

## 2) Node Enrollment

### 2.1 Enroll node
- **Method**: `POST`
- **Route**: `/api/v1/admin/nodes/enroll`
- **Request schema**:
  - `node_id: string (3..128)`
  - `display_name: string (1..128)`
  - `pubkey_fingerprint?: string (<=128)`
- **Response schema**:
  - `id, node_id, display_name, pubkey_fingerprint, enrollment_status, created_at`
- **Auth requirement**: `operator`
- **Validation rules**:
  - reject duplicate active node (`409`)
  - atomic commit with admin audit append
- **Error responses**:
  - `403` role forbidden
  - `409` node already enrolled
  - `422` validation error

---

## 3) Node Registry Listing

### 3.1 List nodes
- **Method**: `GET`
- **Route**: `/api/v1/admin/nodes`
- **Request query**:
  - `limit: int [1..500]`
  - `offset: int >= 0`
- **Response schema**: array of
  - `id, node_id, display_name, enrollment_status, created_at, revoked_at`
- **Auth requirement**: authenticated (`viewer` or `operator`)
- **Validation rules**:
  - bounded pagination params
- **Error responses**:
  - `401` unauthorized
  - `422` invalid query params

---

## 4) Session Reset

### 4.1 Reset current enforcement session
- **Method**: `POST`
- **Route**: `/api/v1/admin/session/reset`
- **Request schema**:
  - `reason: string (5..500)`
- **Response schema**:
  - `current_session_id: string`
  - `session_started_at: datetime`
  - `reset_counter: int`
- **Auth requirement**: `operator`
- **Validation rules**:
  - reason required with minimum length
  - atomic commit with admin audit append
- **Error responses**:
  - `403` role forbidden
  - `422` validation error

---

## 5) Verification Log Listing

### 5.1 List accepted verification records
- **Method**: `GET`
- **Route**: `/api/v1/observability/verification-log`
- **Request query**:
  - `limit`, `offset`
  - `node_id?: string`
  - `session_id?: string`
- **Response schema**: array of
  - `id, session_id, node_id, gateway_received_at, device_timestamp, payload_hash, validation_profile_version, prev_hash, curr_hash`
- **Auth requirement**: authenticated (`viewer` or `operator`)
- **Validation rules**:
  - pagination bounds
- **Error responses**:
  - `401`, `422`

---

## 6) Rejection Log Listing

### 6.1 List rejected records
- **Method**: `GET`
- **Route**: `/api/v1/observability/rejection-log`
- **Request query**:
  - `limit`, `offset`
  - `node_id?: string`
  - `session_id?: string`
  - `rejection_code?: string`
- **Response schema**: array of
  - `id, session_id, node_id, gateway_received_at, rejection_code, rejection_reason, rule_version`
- **Auth requirement**: authenticated (`viewer` or `operator`)
- **Validation rules**:
  - pagination bounds
- **Error responses**:
  - `401`, `422`

---

## 7) Merkle Batch Listing

### 7.1 List Merkle batches
- **Method**: `GET`
- **Route**: `/api/v1/observability/merkle-batches`
- **Request query**:
  - `limit`, `offset`
  - `status?: "pending"|"anchored"|"failed"`
- **Response schema**: array of
  - `id, batch_uuid, session_id, from_verification_id, to_verification_id, leaf_count, merkle_root, status, created_at`
- **Auth requirement**: authenticated
- **Validation rules**:
  - status enum (if provided)
- **Error responses**:
  - `401`, `422`

---

## 8) Blockchain Anchor Listing

### 8.1 List blockchain anchors
- **Method**: `GET`
- **Route**: `/api/v1/observability/anchors`
- **Request query**:
  - `limit`, `offset`
  - `status?: "pending"|"confirmed"|"failed"`
- **Response schema**: array of
  - `id, merkle_batch_id, chain, tx_signature, slot, anchored_at, confirm_status, error_message`
- **Auth requirement**: authenticated
- **Validation rules**:
  - status enum (if provided)
- **Error responses**:
  - `401`, `422`

---

## 9) Verification Detail View

### 9.1 Fetch specific verification record
- **Method**: `GET`
- **Route**: `/api/v1/observability/verification-log/{verification_id}`
- **Request path**:
  - `verification_id: int`
- **Response schema**:
  - `id, session_id, node_id, gateway_received_at, device_timestamp, payload_hash, validation_profile_version, prev_hash, curr_hash, payload_canonical_json`
- **Auth requirement**: authenticated
- **Validation rules**:
  - `verification_id` must be positive integer
- **Error responses**:
  - `401` unauthorized
  - `404` not found
  - `422` invalid path param

---

## 10) Export / Download Audit Artifacts (contract for next implementation)

### 10.1 Create export request
- **Method**: `POST`
- **Route**: `/api/v1/exports`
- **Request schema**:
  - `export_type: "verification_bundle"|"rejection_bundle"|"session_report"`
  - `filters: object` (time range, session_id, node_id)
- **Response schema**:
  - `id: int`
  - `status: "queued"|"completed"|"failed"`
  - `requested_at: datetime`
- **Auth requirement**: `operator`
- **Validation rules**:
  - export_type enum
  - bounded filter ranges
  - append admin audit row (`export_request`)
- **Error responses**:
  - `403`, `422`

### 10.2 Get export request status
- **Method**: `GET`
- **Route**: `/api/v1/exports/{export_id}`
- **Response schema**:
  - `id, status, artifact_path?, artifact_hash?, completed_at?`
- **Auth requirement**: authenticated
- **Error responses**:
  - `401`, `404`

### 10.3 Download export artifact
- **Method**: `GET`
- **Route**: `/api/v1/exports/{export_id}/download`
- **Response schema**:
  - file stream (zip/json/csv)
- **Auth requirement**: `operator`
- **Validation rules**:
  - export must be `completed`
- **Error responses**:
  - `403`, `404`, `409` (not ready)

---

## 11) Health / Status Endpoints

### 11.1 Liveness
- **Method**: `GET`
- **Route**: `/api/v1/health/live`
- **Response schema**: `{ "status": "ok" }`
- **Auth requirement**: none
- **Error responses**: none expected

### 11.2 Readiness
- **Method**: `GET`
- **Route**: `/api/v1/health/ready`
- **Response schema**: `{ "status": "ready" }`
- **Auth requirement**: none
- **Validation rules**:
  - DB ping succeeds (`SELECT 1`)
- **Error responses**:
  - `503` if dependency checks are introduced/fail later

---

## 12) Dashboard Summary Endpoint

### 12.1 Gateway observability summary
- **Method**: `GET`
- **Route**: `/api/v1/observability/dashboard-summary`
- **Response schema**:
  - `total_verified: int`
  - `total_rejected: int`
  - `active_nodes: int`
  - `latest_merkle_root: string | null`
  - `latest_anchor_status: string | null`
- **Auth requirement**: authenticated
- **Validation rules**:
  - none beyond auth
- **Error responses**:
  - `401`
