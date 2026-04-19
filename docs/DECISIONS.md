# Architecture Decision Records

This document captures the key decisions made during Rally's development, the reasoning behind them, and how they evolved as we learned more about the problem.

---

## ADR-001: Core Value Proposition — Relational Organizing, Not Turf Cutting

**Date:** 2026-04-16
**Status:** Active

**Context:** We initially scoped Rally as a "campaign-in-a-box" field operations platform — a free VAN replacement. The original spec prioritized turf cutting (algorithmic division of voter lists into walkable territories) as the centerpiece feature.

**Decision:** The core value of Rally is **relational organizing** — mapping who knows who at the grassroots level so campaigns can activate the right volunteer to reach the right low-turnout voter through a personal relationship.

**Reasoning:** Research shows a friend contacting a voter produces a 13-point turnout increase vs. 2-3 points for a stranger door-knock. The platform's long-term value isn't in replacing VAN's turf-cutting — it's in building a persistent relational graph that compounds across election cycles. When a volunteer uploads their phone contacts and the system matches them against the voter file, you can see which low-propensity voters are reachable through personal relationships. That graph survives after the election and gets richer with every campaign.

**Consequences:**
- Turf cutting map UI was deprioritized (dropped from immediate roadmap)
- Relational organizing module (contact upload → voter matching → outreach suggestions) is the highest-priority feature after the basic organizer dashboard
- The persistent network layer is the architectural differentiator, not the field ops tooling

---

## ADR-002: Two Frontends, One Backend

**Date:** 2026-04-16
**Status:** Active

**Context:** Should volunteers and organizers use the same app?

**Decision:** Two separate frontends — a React web dashboard for organizers and a Flutter mobile app for volunteers — sharing a single FastAPI backend.

**Reasoning:** Volunteers and organizers have fundamentally different jobs. The organizer needs to import voter files, build target lists, manage volunteers, and view analytics. The volunteer needs to see one door at a time and tap big buttons. Combining them means building a permission system complex enough to hide 80% of the app from 90% of the users. Simpler to build two thin frontends on the same API.

The deeper reason: **volunteers should never touch raw data.** The #1 data corruption problem in campaigns is volunteers opening CSVs in Excel and accidentally sorting one column, deleting rows, or duplicating contacts. The mobile app is an ATM, not a database — constrained UI, structured inputs, append-only writes. The organizer dashboard is the control plane.

**Consequences:**
- Backend is a single FastAPI monolith (not microservices)
- Mobile app is offline-first with SQLite local DB, syncs to backend
- Dashboard is a standard React SPA
- Role-based access enforced at the API layer, not the UI layer

---

## ADR-003: State Adapter Pattern for Voter Files

**Date:** 2026-04-16
**Status:** Active

**Context:** Every state publishes voter files in a different format — different column names, delimiters, encodings, date formats, and data availability.

**Decision:** Abstract voter file parsing behind a `StateAdapter` base class. Each state gets its own adapter (e.g., `OhioAdapter`) that implements `parse_row()` to normalize its format into a uniform schema.

**Reasoning:** Adding a new state should require writing one adapter file, not touching the import pipeline, database schema, or any UI code.

**Implementation:**
- `backend/app/adapters/base.py` — base class with shared logic (party normalization, gender normalization)
- `backend/app/adapters/ohio.py` — Ohio SOS voter file parser
- `backend/app/adapters/__init__.py` — registry mapping state codes to adapter classes
- New state = new file + one line in the registry

**Ohio-specific notes:**
- Files are per-county, comma-delimited (quoted), latin-1 encoded
- Date format is YYYY-MM-DD (not what you'd guess from a government file)
- Vote history is encoded in dynamic columns: `GENERAL-11/05/2024`, `PRIMARY-03/19/2024`, etc.
- Values in vote history columns: `X` = voted nonpartisan, `R`/`D`/etc. = party pulled in primary, blank = didn't vote
- Ohio doesn't include gender in the voter file
- Files are free from the Ohio SOS: https://www6.ohiosos.gov/ords/f?p=VOTERFTP:HOME

---

## ADR-004: PostgreSQL + PostGIS

**Date:** 2026-04-16
**Status:** Active

**Context:** The platform needs spatial queries (geocoding, turf cutting, proximity searches for relational organizing) and also standard relational data (users, campaigns, contact results).

**Decision:** PostgreSQL with PostGIS extension, running in a Docker container (`postgis/postgis:16-3.4`).

**Reasoning:** PostGIS handles spatial indexing (GIST indexes on voter locations and turf boundaries) natively. No need for a separate geospatial service. PostgreSQL is battle-tested for the relational side. Single database, no data sync issues.

**Note:** Alembic migrations must exclude PostGIS internal tables (tiger geocoder, spatial_ref_sys, etc.) — see `migrations/env.py` `EXCLUDE_TABLES` set.

---

## ADR-005: Append-Only Contact Results

**Date:** 2026-04-16
**Status:** Active

**Context:** When a volunteer records a contact result (knocked door, got a "Strong Support"), should we update the voter record or create a new row?

**Decision:** Contact results are append-only. Every contact attempt is a new row in `contact_results` with a timestamp. The `campaign_voters` table holds the *latest* support level for quick targeting, but the full history is always preserved.

**Reasoning:**
- Audit trail: you can see every interaction with a voter across time
- Rollback: if a volunteer's data is bad, you can undo their entire shift without losing other data
- Analytics: you can track persuasion over time (did support shift after 3 contacts?)
- Data integrity: no race conditions from two volunteers updating the same record

---

## ADR-006: Turf Cutting Deprioritized

**Date:** 2026-04-19
**Status:** Active

**Context:** The original plan included a map-based turf cutting UI (Phase 1) with algorithmic territory division, walk route optimization, and drag-to-adjust boundaries.

**Decision:** Dropped from immediate roadmap. Basic turf creation (organizer picks voters, names the turf) works through the API and dashboard. The visual map UI is deferred.

**Reasoning:** Turf cutting serves the traditional stranger-canvass model. Relational organizing — where volunteers contact people they personally know — is the higher-impact intervention and the platform's differentiator. Building a fancy map UI for turf cutting before the relational module exists would be optimizing the wrong thing.

Campaigns can still create turfs manually and print walk sheets. The auto-cut algorithm and map UI can be added later when the core relational features are solid.

---

## ADR-007: POC for Ohio Grassroots Organizers

**Date:** 2026-04-19
**Status:** Active

**Context:** Grassroots organizers in Ohio are struggling with voter data management — spreadsheet chaos, lost canvass results, uncoordinated volunteers. They need something usable for the 2026 election cycle.

**Decision:** Pivot from "build the full platform then launch" to "ship a usable POC this week for real organizers."

**What they need immediately:**
1. Voter file browser with county/district/precinct filtering (done — searchable dropdowns)
2. Voter file import UI (done — admin page)
3. Campaign creation from the dashboard
4. Member management (invite volunteers, assign roles)
5. Canvass result entry from the dashboard (after-shift data entry)
6. CSV/PDF export of voter lists and walk sheets

**What can wait:**
- Mobile canvassing app (they'll enter results at HQ for now)
- Relational organizing module
- Turf cutting map
- Geocoding

**Consequences:** Feature priority is now driven by "what do these organizers need this week" rather than the original phased plan.

---

## ADR-008: Searchable Dropdown Filters

**Date:** 2026-04-19
**Status:** Active

**Context:** The voter browser initially used free-text input fields for county, district, and precinct filters. Users had to know the exact value to type.

**Decision:** Replaced with searchable dropdown components backed by lookup API endpoints that return distinct values from the database. Dropdowns cascade — selecting a county filters the district and precinct options.

**Reasoning:** Non-technical organizers shouldn't need to memorize county names or district codes. The dropdown shows them what's available. Cascading prevents invalid combinations (e.g., selecting a precinct that doesn't exist in the chosen county).

**Implementation:**
- `GET /api/v1/lookups/counties` — all distinct counties
- `GET /api/v1/lookups/districts?county=STARK` — districts within a county
- `GET /api/v1/lookups/precincts?county=STARK&district=OH-HD-49` — precincts within county/district
- `SearchableSelect` React component — type-ahead search, click to select, × to clear

---

## ADR-009: No Fundraising Module

**Date:** 2026-04-16
**Status:** Active

**Context:** The original research identified fundraising technology (ActBlue integration, donor CRM, automated email sequences) as a potential feature.

**Decision:** Rally does not build fundraising features. Campaigns link to ActBlue/Anedot directly.

**Reasoning:** Step 2 of the 5-step algorithm: delete the part. ActBlue already works. Donor CRM is a different product for a different user. Building fundraising features would double the scope without advancing the core mission (relational organizing + voter contact management). Campaigns already have a fundraising workflow — they don't have a voter data workflow.
