# AEGIS Backend

FastAPI backend for the AEGIS gateway website/database layer.

## Quick start

1. Create a virtual environment (Python 3.11+).
2. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```
3. Copy environment template:
   ```bash
   cp .env.example .env
   ```
4. Run migrations:
   ```bash
   alembic upgrade head
   ```
5. Run API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Current endpoints

- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `POST /api/v1/auth/bootstrap` (only works when there are zero users)
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/operator-check`
- `POST /api/v1/admin/nodes/enroll` (operator only)
- `GET /api/v1/admin/nodes` (authenticated users)
- `POST /api/v1/admin/session/reset` (operator only)

## Phase 4 status

- Added node enrollment API with operator-only guard and append-only admin action logging.
- Added session reset API with operator-only guard and append-only admin action logging.
- Added node registry listing API for authenticated observability users.

- Admin write operations commit domain mutation and audit append atomically.
