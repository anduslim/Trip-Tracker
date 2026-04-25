# Trip Price Tracker

Personal app to plan a holiday and track flight prices over time.

## Phase 1 MVP

- Email/password auth (JWT in HttpOnly cookie)
- Create/edit/delete holidays
- Add manual flight entries to a holiday with a source URL
- Record price snapshots over time and view a price-history chart
- Trigger a manual price refresh (records a new snapshot)

Phase 2 (next): live search via Amadeus + SerpApi (Google Flights), background
auto-refresh, in-app + email notifications, secure share URLs.

## Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2 (async), Alembic, SQLite (dev) / Postgres (prod)
- **Frontend**: React + Vite + TypeScript, React Router, TanStack Query, Recharts
- **Tests**: pytest + httpx, Vitest + React Testing Library

## Quick start

```bash
make install        # install backend (.venv) and frontend deps
cp .env.example .env
make migrate        # run Alembic migrations
make seed           # create demo user demo@example.com / password123
make dev            # run backend (:8000) and frontend (:5173) concurrently
make test           # run backend + frontend tests
```

See `docs/` (TBD) and the plan file for design notes.
