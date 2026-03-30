# AEGIS Backend (Initial Scaffold)

This folder contains the FastAPI backend scaffold for the AEGIS website/database layer.

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
4. Run API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Current endpoints

- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

## Notes

- SQLite is configured with WAL mode via SQLAlchemy connection event.
- This is Phase 1 scaffold; business modules and migrations are added incrementally.
