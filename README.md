# Rally

**Permanent grassroots organizing infrastructure for state legislative campaigns.**

Rally maps who knows who at the grassroots level — so campaigns can activate the right volunteer to reach the right low-turnout voter through a personal relationship, not a stranger at the door.

## The Problem

State representative races are decided by hundreds of votes. The proven way to move those votes is personal contact — but not from strangers. A friend asking you to vote produces a **13-point turnout increase**. A stranger knocking your door produces 2-3 points. The difference wins or loses elections.

The problem is that campaigns have no way to see these relationships. They don't know that volunteer Sarah went to high school with 40 registered voters in precinct 5, or that volunteer Mike's church small group includes 12 people who haven't voted in a midterm since 2018.

And when the election ends, everything disappears. The next candidate in that district starts from zero — no volunteer network, no relational map, no institutional knowledge.

## What Rally Does

**Rally builds a persistent map of who knows who.** Volunteers upload their phone contacts. The system matches those contacts against the voter file. Suddenly you can see: "Sarah knows 23 registered voters in this district. 8 of them are low-turnout persuadables. Here's a talking point for each one."

This relational graph **compounds across election cycles.** Every campaign that uses Rally adds more connections to the map. Over time, you have a complete picture of the social fabric of a district — who the connectors are, which voters are reachable through personal relationships, and which volunteers have proven track records.

### The Platform

Rally is two products sharing one backend:

**Organizer Dashboard** (web) — Campaign managers use this to:
- Import and browse voter files (Ohio supported, 50-state architecture)
- Build target voter lists by filtering on district, party, vote history, precinct
- Create canvass surveys and scripts
- Track campaign field metrics (doors knocked, contact rate, voter IDs, support breakdown)

**Volunteer App** (mobile, coming soon) — Volunteers use this to:
- Upload phone contacts and see which of their friends are registered voters
- Get prioritized outreach suggestions ("Call your friend Sarah — she's voted in 1 of 4 elections")
- Canvass assigned turfs with an offline-first mobile app
- Record contact results through a constrained UI (big buttons, one voter at a time — volunteers never touch raw data)

**Persistent Network Layer** — The infrastructure that survives between campaigns:
- Volunteer profiles with reliability history and skills
- Relational graph: who knows who, who can reach who
- Aggregated voter contact intelligence (precinct-level, not individual)
- Operational knowledge (which apartments are gated, where you need Spanish scripts)

## Why State Races

- Median state house campaign budget: **$15,000-$50,000** (no money for VAN licenses or consultants)
- Typical tech stack: **a personal Gmail and a clipboard**
- Winning margins: **often under 1,000 votes**
- State legislatures control **redistricting, 70%+ of US law, and are the pipeline to Congress**

Rally is free. It's built for a candidate running their first race who can't afford a $3,000 VAN license and doesn't have a field director.

## Architecture

```
┌─────────────────────┐     ┌──────────────────────┐
│  Volunteer App       │     │  Organizer Dashboard  │
│  (Flutter, mobile)   │     │  (React, web)         │
│  - Offline-first     │     │  - Voter file mgmt    │
│  - Contact upload    │     │  - List building      │
│  - Canvass capture   │     │  - Turf management    │
│  - Relational        │     │  - Analytics/QA       │
│    outreach          │     │  - Survey builder     │
└────────┬────────────┘     └──────────┬───────────┘
         │                              │
         └──────────┬──────────────────┘
                    │ REST API
         ┌──────────▼──────────────────┐
         │  Backend (Python/FastAPI)    │
         │  - Auth & multi-tenancy     │
         │  - Voter file processing    │
         │  - Contact matching         │
         │  - Relational graph         │
         │  - Network layer            │
         └──────────┬──────────────────┘
                    │
         ┌──────────▼──────────────────┐
         │  PostgreSQL + PostGIS       │
         └──────────┬──────────────────┘
                    │
         ┌──────────▼──────────────────┐
         │  External Services          │
         │  - Geocodio (geocoding)     │
         │  - Twilio (SMS)             │
         │  - Census TIGER (maps)      │
         │  - L2 (voter files)         │
         └─────────────────────────────┘
```

**Key design decisions:**
- One backend, two thin frontends, monolith (not microservices)
- Multi-tenant: each campaign is isolated, shared network layer is opt-in and aggregated
- Volunteers never touch raw data — constrained UIs with structured inputs only
- Contact results are append-only (never updated, never deleted)
- State adapter pattern: one adapter per state's voter file format, uniform output

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0 |
| Database | PostgreSQL 16 + PostGIS |
| Dashboard | React, TypeScript, Vite |
| Mobile App | Flutter (planned) |
| Geocoding | Geocodio |
| Auth | JWT + bcrypt |

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+
- Docker (for PostgreSQL + PostGIS)

### Setup

```bash
# Start the database
docker-compose up -d db

# Backend
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head

# Create an admin user
python -m app.cli create-admin --email you@example.com --password yourpassword --name "Your Name"

# Import a voter file (Ohio example)
# Download from https://www6.ohiosos.gov/ords/f?p=VOTERFTP:HOME
python -m app.cli import-voters --state OH --file /path/to/COUNTY.txt

# Start the backend
uvicorn app.main:app --reload

# Dashboard (in a separate terminal)
cd dashboard
npm install
npm run dev
```

### Voter File Sources

Ohio voter files are free from the Secretary of State: https://www6.ohiosos.gov/ords/f?p=VOTERFTP:HOME

Files are per-county, comma-delimited. The Ohio adapter handles parsing automatically.

## Project Structure

```
rally/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── cli.py            # Admin CLI
│   │   ├── core/             # Config, database, auth, dependencies
│   │   ├── models/           # SQLAlchemy models
│   │   ├── api/              # Routes and schemas
│   │   ├── services/         # Business logic
│   │   └── adapters/         # State voter file parsers
│   └── migrations/           # Alembic migrations
├── dashboard/                # React organizer dashboard
└── mobile/                   # Flutter volunteer app (planned)
```

## Roadmap

### Done
- [x] Backend: auth, multi-tenancy, campaign management
- [x] Backend: Ohio voter file adapter + import pipeline (tested: Ashland 33K, Stark 244K voters)
- [x] Backend: Geocoding pipeline (Geocodio)
- [x] Backend: Voter targeting, turf creation, canvass results, surveys
- [x] Backend: Lookup endpoints with cascading filters (county → district → precinct)
- [x] Dashboard: Auth, voter browser with searchable dropdowns, list builder, survey builder, campaign stats
- [x] Dashboard: Voter file import UI (admin)

### In Progress — POC for Ohio organizers
- [ ] Dashboard: Campaign creation UI
- [ ] Dashboard: Member management (invite volunteers, assign roles)
- [ ] Dashboard: Canvass result entry (after-shift data entry from laptop)
- [ ] Dashboard: CSV/PDF export of voter lists and walk sheets

### Next — Core differentiator
- [ ] Relational organizing: contact upload → voter file matching → outreach suggestions
- [ ] Persistent network layer: volunteer profiles, relational graph, precinct knowledge across cycles
- [ ] Mobile volunteer app (Flutter, offline-first canvassing + relational outreach)

### Future
- [ ] P2P texting (10DLC compliant)
- [ ] Turf cutting map UI (auto-divide target lists into walkable territories)
- [ ] Additional state adapters
- [ ] Anomaly detection + QA sampling for canvass data quality

## Decision Log

See [docs/DECISIONS.md](docs/DECISIONS.md) for architecture decision records covering:
- Why relational organizing is the core value, not turf cutting
- Two frontends / one backend design
- State adapter pattern
- Append-only contact results
- POC-first approach for Ohio organizers

## License

TBD
