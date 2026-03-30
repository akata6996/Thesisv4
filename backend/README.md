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

## Phase 3 status

- Added JWT-based local auth flow with PBKDF2 password hashing (passlib).
- Added role guard dependency for operator-only endpoints.
- Added append-only admin audit logging service and wired login events (`user_login`) into `admin_action_log`.
