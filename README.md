# Trip Price Tracker

Personal app to plan a holiday and track flight prices over time.

## Features

- Email/password auth (JWT in HttpOnly cookie) plus CSRF double-submit cookie protection on every mutating request; each holiday is owner-scoped
- Create/edit/delete holidays with destinations, dates, currency, and per-holiday change thresholds
- Add flight entries (manual or saved from a search) with source URL and price
- Live flight search via a pluggable provider (Amadeus default, SerpApi/Google Flights when `SERPAPI_KEY` is set, FakeFlightProvider as a credentials-free fallback)
- Single-route search (one-way or return) and multi-city search:
  - **Separate tickets per leg**: 2–8 legs searched in parallel; cheapest combined total shown when every leg has results
  - **Single ticket (one PNR)**: a single Amadeus itinerary covering all legs in order; best for connecting trips. Saves all legs into the holiday as a group
- Price-context for single-route searches: Amadeus historical-price quartiles (min/25%/median/75%/max) shown as a panel and per-offer **Bargain / Good price / Typical / Expensive** badges (skipped silently for providers without analytics, e.g. SerpApi)
- Trip-duration filter (min/max days) on top of provider results
- Background jobs (APScheduler in-process):
  - `refresh_tracked_prices` re-fetches prices via the entry's original provider
  - `dispatch_email_queue` sends queued email notifications (console / SMTP)
  - `prune_old_snapshots` downsamples snapshots older than 90 days to one per day
- In-app feed + email alerts when a tracked entry's price moves more than the configured percent / absolute threshold
- Comparison view: route grouping, cheapest route, biggest 30-day drop, best day-of-week to depart (when there are enough samples)
- Secure share URLs: rotatable, revocable, read-only; revoked or unknown tokens return HTTP 410
- Public read-only endpoints rate-limited per client IP

## Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2 (async), Alembic, SQLite (dev) / Postgres (prod), APScheduler
- **Frontend**: React + Vite + TypeScript, React Router, TanStack Query, Recharts
- **Tests**: pytest + httpx (27 cases), Vitest + React Testing Library

## Quick start (local dev)

```bash
make install        # creates backend/.venv and installs frontend deps
cp .env.example .env
make migrate        # apply Alembic migrations
make seed           # creates demo@example.com / password123
make backend        # runs API on :8000
make frontend       # runs UI on :5173 (separate terminal)
make test           # backend + frontend tests
```

To enable Phase 2/3 features locally, set in `.env`:

```
AMADEUS_CLIENT_ID=...
AMADEUS_CLIENT_SECRET=...
SERPAPI_KEY=...        # optional; enables Google Flights via SerpApi
SCHEDULER_ENABLED=true # turn on the auto-refresh + email + prune jobs
```

When `DEBUG=true`, three debug-only endpoints are exposed for manual triggering:

- `POST /api/dev/refresh`
- `POST /api/dev/dispatch-emails`
- `POST /api/dev/prune-snapshots`

## Deploy (single VM, docker-compose)

```bash
cp .env.example .env   # set SECRET_KEY, PUBLIC_BASE_URL, POSTGRES_PASSWORD, providers
docker compose -f docker-compose.prod.yml up -d --build
```

The compose stack ships three services:

- `db` — Postgres 16 with a persistent `pg_data` volume
- `api` — backend image, runs `alembic upgrade head` then `uvicorn`. **Single replica only** because APScheduler runs in-process; if you need to scale beyond one container, switch the scheduler off and add a Celery beat worker instead
- `web` — nginx serving the built frontend and proxying `/api/*` to `api:8000`

Front the stack with TLS termination (Caddy or nginx + certbot) before exposing publicly.

## Project layout

```
backend/
  app/
    config.py              pydantic-settings
    db.py                  async engine + SessionLocal
    main.py                FastAPI app factory + lifespan
    deps.py                FastAPI deps (current_user, db)
    security.py            password hashing + JWT
    models/                SQLAlchemy 2 models
    schemas/               Pydantic request/response models
    routers/               auth, holidays, flights, search, share, public, notifications, dev, health
    services/              flight_provider + amadeus/serpapi/fake providers, price_tracker, comparison_engine, share_service, notifier
    middleware/            public rate limit
    jobs/                  APScheduler wiring
    seeds/seed_dev.py
  alembic/                 migrations
  tests/
frontend/
  src/
    api/                   fetch wrappers per resource
    components/            ProtectedRoute, AppShell, FlightEntryForm, PriceHistoryChart, ShareLinkPanel
    context/AuthContext.tsx
    pages/                 Login, Register, HolidaysList, HolidayDetail, FlightSearch, Comparison, Notifications, PublicShare, NotFound
    router.tsx
    types/api.ts
infra/                     (reserved for future deploy scripts)
docker-compose.prod.yml
```

## Implementation phases

- **Phase 1 (MVP)**: auth, holidays CRUD, manual flight entries, snapshots + chart, manual refresh
- **Phase 2**: provider abstraction (Amadeus + SerpApi + Fake), search, save-offer, scheduler, in-app + email notifications, share tokens, comparison view
- **Phase 3**: trip-duration filter, best-day-of-week insight, snapshot pruning, public rate limit, debug endpoints, Dockerfiles + docker-compose.prod.yml

## Open follow-ups

- Playwright end-to-end suite (register → create holiday → save offer → chart → share link)
- Celery + Redis migration when more than one `api` replica is needed
