# Rally — Grassroots Organizing Infrastructure

> **Note**: Inherits DOEM framework from the workspace root CLAUDE.md.

## What This Is

Rally maps who knows who at the grassroots level — so campaigns can activate the right volunteer to reach the right low-turnout voter through a personal relationship. The core value is the **relational graph** that compounds across election cycles, not the field ops tooling (which is table stakes).

Currently being POC'd with Ohio grassroots organizers for the 2026 cycle.

## Architecture

- **Backend**: Python 3.13 / FastAPI, PostgreSQL 16 + PostGIS
- **Dashboard**: React / TypeScript / Vite (organizer-facing, web)
- **Mobile App**: Flutter (volunteer-facing, offline-first — planned, not started)
- **One backend, two thin frontends, monolith**

## Project Structure

```
rally/
├── CLAUDE.md              # This file
├── README.md              # Public-facing docs
├── docs/DECISIONS.md      # Architecture decision records
├── docker-compose.yml     # PostgreSQL + PostGIS
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app entry point
│   │   ├── cli.py         # Admin CLI (import voters, create admin)
│   │   ├── core/          # Config, database, auth (JWT+bcrypt), dependencies
│   │   ├── models/        # SQLAlchemy models (13 tables)
│   │   ├── api/
│   │   │   ├── schemas.py # Pydantic request/response schemas
│   │   │   └── routes/    # auth, campaigns, voters, turfs, canvass, surveys, lookups, admin
│   │   ├── services/      # geocoding (Geocodio), voter_import
│   │   └── adapters/      # State voter file parsers (base.py + ohio.py)
│   ├── migrations/        # Alembic (PostGIS tables excluded via EXCLUDE_TABLES)
│   └── pyproject.toml
├── dashboard/             # React organizer dashboard
│   └── src/
│       ├── api/           # Axios client + TypeScript types
│       ├── components/    # Layout, ProtectedRoute, SearchableSelect
│       ├── context/       # AuthContext, CampaignContext
│       └── pages/         # auth, campaign, voters, turfs, surveys, admin
└── mobile/                # Flutter volunteer app (planned)
```

## Key Commands

```bash
# Start database
docker-compose up -d db

# Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload

# CLI
python -m app.cli create-admin --email admin@rally.org --password xxx --name "Admin"
python -m app.cli import-voters --state OH --file /path/to/COUNTY.txt [--geocode]

# Migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Dashboard
cd dashboard && npm run dev
```

## Data Model

13 tables: `voters` (master file, partitioned by state), `campaigns` (tenants), `campaign_voters` (per-campaign targeting), `contact_results` (append-only), `turfs` + `turf_voters`, `users` + `campaign_members` (persistent identities, per-campaign roles), `surveys` + `survey_questions`, `audit_log`, `volunteer_contacts` (relational graph), `precinct_notes` (shared knowledge).

## Design Principles

1. **Relational organizing is the core.** Mapping who-knows-who matters more than turf cutting or canvass logistics.
2. **Volunteers never touch raw data.** Constrained UIs, structured inputs, append-only writes. No CSVs in volunteer hands.
3. **The network persists.** Volunteer profiles, relational maps, and precinct knowledge survive across campaigns and election cycles.
4. **Campaign isolation by default.** Multi-tenant. Shared network layer is opt-in and aggregated.
5. **State adapter pattern.** One adapter per state's voter file format. Adding a state = one file.

## Ohio Voter File Notes

- Free from Ohio SOS: https://www6.ohiosos.gov/ords/f?p=VOTERFTP:HOME
- Per-county, comma-delimited (quoted fields), latin-1 encoded
- Date format: YYYY-MM-DD
- Vote history in dynamic columns: `GENERAL-11/05/2024`, `PRIMARY-03/19/2024`
- Values: X = voted nonpartisan, R/D/etc = party pulled in primary, blank = didn't vote
- No gender field
- Currently loaded: Ashland (33,451), Stark (243,893)

## Current Status

**Phase 1 (organizer dashboard) — mostly complete:**
- [x] Auth, campaigns, multi-tenancy
- [x] Voter file browser with searchable county/district/precinct dropdowns
- [x] List builder (add to target universe by selection or filter)
- [x] Surveys/scripts
- [x] Campaign stats dashboard
- [x] Voter file import UI (admin)
- [ ] Campaign creation UI
- [ ] Member management UI
- [ ] Canvass result entry from dashboard
- [ ] CSV/PDF export

**POC blockers (need this week for Ohio organizers):**
- Campaign creation, member management, result entry, export

**Next after POC:**
- Relational organizing module (contact upload → voter matching → outreach suggestions)
- Mobile volunteer app (Flutter, offline-first)
- Persistent network layer

## Decision Log

See `docs/DECISIONS.md` for full architecture decision records.
