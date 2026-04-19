# Rally — Field Operations Platform

> **Note**: Inherits DOEM framework from the workspace root CLAUDE.md.

## What This Is

Rally is a free field operations platform for state legislative campaigns + a persistent organizing network that compounds volunteer/voter intelligence across election cycles. Think "Shopify for state campaigns" — the VAN replacement that first-time candidates can actually use.

## Architecture

- **Backend**: Python/FastAPI, PostgreSQL + PostGIS
- **Mobile App**: Flutter (volunteer-facing, offline-first canvassing)
- **Dashboard**: React (organizer-facing, web)
- **One backend, two frontends, monolith**

## Project Structure

```
rally/
├── CLAUDE.md              # This file
├── docker-compose.yml     # PostgreSQL + PostGIS + backend
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app
│   │   ├── cli.py         # Admin CLI (import voters, create admin)
│   │   ├── core/          # Config, database, auth, dependencies
│   │   ├── models/        # SQLAlchemy models (voter, campaign, turf, etc.)
│   │   ├── api/           # Routes and Pydantic schemas
│   │   ├── services/      # Business logic (geocoding, voter import)
│   │   └── adapters/      # State voter file parsers (Ohio first)
│   ├── migrations/        # Alembic migrations
│   └── pyproject.toml
├── dashboard/             # React organizer dashboard (Phase 1)
└── mobile/                # Flutter volunteer app (Phase 2)
```

## Key Commands

```bash
# Start services
docker compose up -d

# Run backend locally
cd backend && uvicorn app.main:app --reload

# Create admin user
python -m app.cli create-admin --email admin@rally.org --password xxx --name "Admin"

# Import Ohio voter file
python -m app.cli import-voters --state OH --file /path/to/county.csv --geocode

# Run migrations
cd backend && alembic upgrade head

# Generate new migration
cd backend && alembic revision --autogenerate -m "description"
```

## Data Model

Core tables: `voters` (master file), `campaigns` (tenants), `campaign_voters` (per-campaign targeting), `contact_results` (append-only contact log), `turfs` (walkable territories), `users`/`campaign_members` (persistent identities with per-campaign roles), `surveys`/`survey_questions`, `audit_log`, `volunteer_contacts` (relational graph), `precinct_notes` (shared knowledge).

## Design Principles

1. **Volunteers never touch raw data.** They interact through constrained UIs — big buttons, one record at a time, structured inputs only.
2. **Append-only contact results.** Never update or delete contact records. Every interaction is a new row with a timestamp.
3. **Campaign isolation by default.** Multi-tenant: campaigns can't see each other's data. The shared network layer is opt-in and aggregated.
4. **Offline-first mobile.** The canvassing app must work with zero cell signal. SQLite local DB, sync when connected.
5. **State adapter pattern.** Each state's voter file is different. One adapter per state, uniform output.

## Current Phase

Phase 0: Foundation — backend scaffold, models, auth, Ohio adapter, geocoding pipeline.
