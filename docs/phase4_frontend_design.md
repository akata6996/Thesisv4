# AEGIS Phase 4 Frontend Design (Web UI)

This document defines the page-level design for the gateway-local React UI.

## UI architecture assumptions
- Frontend stack: React + Vite + Tailwind + React Query.
- API base: `/api/v1`.
- Auth: JWT bearer token stored in memory + secure local storage fallback.
- Access tiers:
  - `viewer`: observability pages only.
  - `operator`: observability + admin actions (enroll/reset/export).
- UI never writes verification/rejection records directly.

## Shared layout pattern
- **Top bar**: gateway name, user identity, role badge, logout.
- **Side nav**:
  - Dashboard
  - Verification Log
  - Rejection Log
  - Merkle Batches
  - Blockchain Anchors
  - Verification Workspace
  - Node Registry
  - Node Enrollment (operator)
  - Session Reset (operator)
  - Export (operator)
  - System Status
- **Common table controls**: search, filters, pagination, CSV download of current view.

---

## 1) Login Page
### Purpose
Authenticate local viewer/operator users.

### Key UI components
- Username input
- Password input
- Login button
- Inline error banner

### Data displayed
- Validation errors
- Auth failure message

### User role access
- Public (pre-auth)

### Actions allowed
- Submit credentials
- Optional bootstrap-first-operator flow if no users exist

### API endpoints used
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/bootstrap` (conditional UX path)
- `GET /api/v1/auth/me` (post-login verification)

---

## 2) Dashboard
### Purpose
High-level operational observability at a glance.

### Key UI components
- KPI cards (`total_verified`, `total_rejected`, `active_nodes`)
- Latest Merkle root card
- Latest anchor status card
- Mini trend widgets (future enhancement)

### Data displayed
- Dashboard summary aggregates

### User role access
- Viewer + Operator

### Actions allowed
- Navigate to logs, anchors, batches
- Refresh summary

### API endpoints used
- `GET /api/v1/observability/dashboard-summary`

---

## 3) Node Enrollment Page
### Purpose
Operator onboarding of node identity into registry.

### Key UI components
- Enrollment form (`node_id`, `display_name`, `pubkey_fingerprint`)
- Submit button
- Success/error toast
- Recent enrollments panel

### Data displayed
- Form validation errors
- Last enrolled nodes

### User role access
- Operator only

### Actions allowed
- Create enrollment request

### API endpoints used
- `POST /api/v1/admin/nodes/enroll`
- `GET /api/v1/admin/nodes`

---

## 4) Node Registry Page
### Purpose
Inspect all known node records and status.

### Key UI components
- Table with status chips
- Filter bar (status, node_id)
- Pagination controls

### Data displayed
- `node_id`, `display_name`, `enrollment_status`, `created_at`, `revoked_at`

### User role access
- Viewer + Operator

### Actions allowed
- Read/search/filter only (revoke planned separately)

### API endpoints used
- `GET /api/v1/admin/nodes`

---

## 5) Session Reset Page
### Purpose
Operator-triggered enforcement session rotation with audit reason.

### Key UI components
- Reason text area
- Confirmation modal
- Result panel showing new `current_session_id` and `reset_counter`

### Data displayed
- Reset response metadata
- Error state

### User role access
- Operator only

### Actions allowed
- Submit reset command

### API endpoints used
- `POST /api/v1/admin/session/reset`

---

## 6) Verification Log Page
### Purpose
Browse accepted, hash-linked verification records.

### Key UI components
- Paginated table
- Filters (`node_id`, `session_id`)
- Row action: open detail/proof workspace

### Data displayed
- `id`, `session_id`, `node_id`, timestamps, payload hash, `prev_hash`, `curr_hash`

### User role access
- Viewer + Operator

### Actions allowed
- Read/filter/paginate
- Open record detail

### API endpoints used
- `GET /api/v1/observability/verification-log`

---

## 7) Rejection Log Page
### Purpose
Investigate rejected packets and rule failures.

### Key UI components
- Paginated table
- Filters (`node_id`, `session_id`, `rejection_code`)
- Row expansion for rejection reason details

### Data displayed
- `id`, `node_id`, `session_id`, `rejection_code`, `rejection_reason`, `rule_version`

### User role access
- Viewer + Operator

### Actions allowed
- Read/filter/paginate

### API endpoints used
- `GET /api/v1/observability/rejection-log`

---

## 8) Merkle Batches Page
### Purpose
Observe batch generation lifecycle for accepted measurements.

### Key UI components
- Table with batch range and status
- Status filter (`pending`, `anchored`, `failed`)

### Data displayed
- `batch_uuid`, id range, leaf count, root, status, created time

### User role access
- Viewer + Operator

### Actions allowed
- Read/filter/paginate

### API endpoints used
- `GET /api/v1/observability/merkle-batches`

---

## 9) Blockchain Anchor Page
### Purpose
Track on-chain anchoring outcomes for Merkle roots.

### Key UI components
- Table with confirm status chips
- Status filter
- External tx link launcher (when tx signature present)

### Data displayed
- `merkle_batch_id`, `tx_signature`, `slot`, `confirm_status`, `error_message`

### User role access
- Viewer + Operator

### Actions allowed
- Read/filter/paginate
- Open explorer link

### API endpoints used
- `GET /api/v1/observability/anchors`

---

## 10) Verification Workspace / Proof Viewer
### Purpose
Operator/analyst workspace for single-record integrity inspection.

### Key UI components
- Record selector / deep-link from table
- Hash-link panel (`prev_hash` -> `curr_hash`)
- Payload viewer (`payload_canonical_json`)
- Copy hash buttons

### Data displayed
- Full verification row details and linked hash metadata

### User role access
- Viewer + Operator

### Actions allowed
- Inspect and copy evidence values

### API endpoints used
- `GET /api/v1/observability/verification-log/{verification_id}`

---

## 11) Export Page
### Purpose
Request and download audit artifacts for panel/demo evidence.

### Key UI components
- Export request form (`export_type`, filters)
- Export jobs table with status
- Download button for completed exports

### Data displayed
- Export request lifecycle (`queued/completed/failed`)
- Artifact metadata (`artifact_hash`, completion time)

### User role access
- Operator only

### Actions allowed
- Create export request
- Poll status
- Download completed artifact

### API endpoints used
- `POST /api/v1/exports` (planned contract)
- `GET /api/v1/exports/{export_id}` (planned contract)
- `GET /api/v1/exports/{export_id}/download` (planned contract)

---

## 12) System Status Page
### Purpose
Gateway health and readiness diagnostics.

### Key UI components
- Liveness card
- Readiness card
- Last check timestamps
- Retry/refresh button

### Data displayed
- API liveness and readiness state

### User role access
- Viewer + Operator

### Actions allowed
- Manual refresh

### API endpoints used
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

---

## Security and UX safeguards
- Hide operator-only nav items for viewers and enforce server-side RBAC anyway.
- Confirm destructive/admin actions with explicit modal confirmation.
- Never expose secret/auth data in logs or UI.
- Keep all write operations through backend service layer (no direct data-plane writes).
