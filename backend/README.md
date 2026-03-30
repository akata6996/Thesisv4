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

## Phase 2 status

- Core SQLAlchemy models added for users, enrollment, session state, verification/rejection logs,
  Merkle/anchor records, admin action log, and audit exports.
- Initial Alembic migration added at `alembic/versions/20260330_0001_initial_phase2_schema.py`.
