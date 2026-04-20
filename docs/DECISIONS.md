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

---

## ADR-010: Three-Tier Data Ownership Model

**Date:** 2026-04-20
**Status:** Active

**Context:** Design questions surfaced around what data Rally retains, what can compound across campaigns and cycles, and what legal constraints apply (FEC coordination rules and state analogs, state comprehensive privacy laws, TCPA). The core tension: Rally's long-term thesis is "voter data gets better every cycle," but campaigns cannot legally share their targeting intelligence with one another without coordinating.

**Decision:** All data in Rally belongs to one of three ownership tiers, enforced by schema and API boundaries.

1. **Platform-owned (compounds indefinitely across all campaigns and cycles).** Derived from public sources or operational reality.
   - `voters` — master voter file. Cleaned, deduped, geocoded, enriched with each cycle's new vote history and registration updates.
   - District/precinct geometry, address standardization, operational geographic notes (broken buzzers, apartment access, bad-geocode corrections).
   - Derived scores from public features (turnout propensity, partisanship inference) — trained on `party × age × vote history × precinct`.
   - Aggregated and de-identified behavioral signal (e.g., "voters in this precinct are reachable 35% of weekday evenings").

2. **Campaign-owned (walled per campaign, ephemeral per cycle).** Generated by a campaign's operational activity. Cannot cross between non-coordinated campaigns without explicit consent.
   - `campaign_voters` — targeting universe and per-campaign scores.
   - `contact_results` — what volunteers heard at the door.
   - `survey_responses` — what the campaign learned.
   - `turfs`, `turf_voters` — strategic walk assignments.

3. **Volunteer-owned (scoped to the user, portable across campaigns they join).**
   - `volunteer_contacts` / relational graph — the user's uploaded contacts, matched to voters.
   - Volunteer profile, skills, preferred shifts, history of past campaigns.
   - Travels with the user when they join a new campaign. Not any campaign's asset.

**Reasoning:**
- **Legal clarity.** FEC coordination rules and state analogs restrict cross-campaign flow of campaign-generated intelligence. The wall between tiers 1 and 2 keeps Rally vendor-clean — vendors are allowed to improve a product using aggregated data from multiple clients (NGP VAN, Catalist, TargetSmart all operate on this model).
- **The compounding thesis stays intact.** 80% of what makes voter data valuable over time is platform-owned work on public records; that compounds indefinitely. Campaign-generated IDs expire with each cycle anyway — losing cross-cycle persistence there costs nothing real.
- **Relational moat.** The volunteer graph is the highest-value long-term asset. Making it volunteer-owned (not campaign-owned) is what lets it survive cycles and campaigns — and sidesteps coordination rules, since the graph belongs to the user, not any campaign.

**Consequences:**
- Campaigns never write directly into `voters`. All campaign-generated data lives in `campaign_*` tables.
- Platform-level enrichment (geocoding corrections, score updates, address normalization) flows into `voters` regardless of which campaign surfaced the issue.
- Volunteer data (`users`, `volunteer_contacts`, relationship edges) reattaches when the same user joins a new campaign.
- TOS and privacy policy must state these three tiers explicitly so campaigns and volunteers know what persists and what does not.

---

## ADR-011: Volunteer Contact Retention — Edges Compound, PII Expires

**Date:** 2026-04-20
**Status:** Active

**Context:** Relational organizing requires volunteers to upload their phone/email contacts so Rally can match them against the voter file and surface outreach suggestions. This creates obligations under TCPA (for any outreach), CCPA/CPRA, VCDPA, and the ~15 other state comprehensive privacy laws in effect as of 2026. It also creates a data liability that grows linearly with volunteers.

**Decision:** Split contact storage into two tables with different retention policies.

1. **`volunteer_contact_uploads` — raw PII, retention-capped.**
   - Raw name, phone, email from the volunteer's contact list.
   - Scoped to the uploading volunteer (`user_id`).
   - Unmatched contacts (no voter-file match) discarded after **90 days**.
   - Matched contacts retained for the life of the volunteer's account, used for re-matching when the voter file updates.
   - Hard-deleted when the volunteer deletes their account or a data subject (the contact themselves) requests deletion.

2. **`volunteer_voter_edges` — durable relationship graph.**
   - Schema: `(user_id, voter_id, relationship_type, source, matched_at, confirmed_by_volunteer_at)`.
   - Points at public voter-file records, so the edge carries no new PII about the contact.
   - Retained indefinitely. Reattaches when the volunteer joins new campaigns.
   - This is what compounds cycle-over-cycle.

**Reasoning:**
- The edges are the durable asset. The raw uploads are a liability (CCPA deletion rights, breach blast radius, retention obligations).
- Separating them lets retention be tuned independently: aggressive on PII, indefinite on edges.
- When a volunteer rejoins for a new cycle, their edges are still there — no re-upload, they just see "12 of your friends are in this campaign's universe."

**Compliance requirements (must ship with the relational module):**
- Explicit consent checkbox at upload; consent timestamp logged.
- Public-facing "delete my data" endpoint (email request + manual handling acceptable for MVP); 30–45 day response SLA.
- Privacy policy that states the three-tier ownership model (ADR-010) and the 90-day unmatched retention.
- Volunteers cannot be used to send Rally-originated calls or texts — all outreach must be volunteer-initiated in the volunteer's own messaging app. Rally's job is to *prompt* outreach, never to *perform* it.

**Consequences:**
- If `volunteer_contacts` currently stores raw PII against `user_id`, refactor into the two-table split before the relational module ships.
- `volunteer_voter_edges` becomes the primary interface for "who does this volunteer know in our universe."
- Any future cross-campaign relational feature queries the edges table scoped to a volunteer's current campaign memberships — raw uploads never leave the volunteer's own scope.

---

## ADR-012: Coordination-Mode Flag for Cross-Campaign Features

**Date:** 2026-04-20
**Status:** Active

**Context:** The Ohio POC involves multiple campaigns running in parallel, sometimes with overlapping geographies and volunteers. Future features (cross-campaign turf deconfliction, coalition calendar, "voter last contacted by any campaign" signal) would require data to flow between campaigns — which is legally fraught under FEC coordination rules and state analogs. Building any such feature without an explicit legal control surface creates compliance risk.

**Decision:** Add an explicit `coordination_mode` flag on the campaign–campaign relationship. Implement via a nullable `coalition_id` on `campaigns` plus a mode enum. Three values:

- **`independent`** — default. Campaigns cannot see each other's data. Only aggregated, de-identified signal flows across (platform tier 1 only).
- **`coordinated`** — both campaigns have legally certified they are coordinated (e.g., federal + state under the same candidate committee structure). Targeting, IDs, and strategic data may be shared.
- **`coalition`** — a shared, county-organizer-style coalition where all participating campaigns have opted in with explicit consent, typically operated under a state or county party's coordinated-campaign structure. Limited shared signals (e.g., "contacted this week") allowed.

**Reasoning:**
- Gets the legal structure correct before any feature ships that depends on it. Retrofitting isolation after data has already flowed is painful and potentially a compliance incident.
- Gives campaign lawyers a recognizable control: "is this campaign flagged `independent` or `coalition`?"
- Schema cost is near-zero; UI cost comes later, only when coalition features ship.

**Consequences:**
- Schema migration before the first coalition-style feature: `campaigns.coalition_id` (nullable FK), `campaign_coordination_mode` enum.
- Coalition onboarding must include a legal affirmation step ("we certify we are operating as a coordinated coalition under [state] election law").
- Any future API endpoint that reads across campaigns must check the coordination flag before returning.

---

## ADR-013: Volunteer-First UX for Parallel Multi-Campaign Operations

**Date:** 2026-04-20
**Status:** Active

**Context:** The Ohio POC runs **multiple campaigns in parallel** — one volunteer may be active on 2–3 races at once. Rally's current data model is campaign-centric (`campaign_voters`, `campaign_members`, turfs scoped to campaign). This breaks down when volunteers work across campaigns: double-booked shifts, competing asks from overlapping universes, fragmented profile across campaigns.

**Decision:** Shift the primary UX axis from campaign-centric to volunteer-centric for anything that spans campaigns. The data model stays campaign-scoped (for isolation); the query and rendering layer treats the volunteer as the anchor.

**Applications:**
1. **Shift calendar.** A volunteer sees one unified calendar across all their campaigns. Prevents double-booking. Data lives per campaign; query is user-scoped.
2. **Relational ask arbitration.** When a volunteer's contact intersects multiple campaign universes, the ask surfaces from the campaign where the voter has highest priority (persuadability × turnout), not whichever campaign loaded first. Prevents campaigns from burning out shared volunteers by competing for the same warm list.
3. **Volunteer profile portability.** Skills, preferences, past-campaign history follow the user. Campaigns see what's relevant to them; the complete history belongs to the volunteer.

**Reasoning:**
- In parallel multi-campaign contexts, the volunteer is the scarce resource. Coordinating *their time* matters more than coordinating campaign resources.
- Building campaign-scoped silos without a user-scoped rendering layer reproduces VAN's core frustration — three logins, three calendars, three notification streams.

**Deferred to post-POC (design-for, don't build yet):**
- Coalition / county-organizer view above campaigns (sketch `coalition_id` in schema now per ADR-012; ship the UI later).
- Cross-campaign turf deconfliction calendar.
- "Voter last contacted by any campaign" aggregated signal (gated behind `coordination_mode=coalition`).

**Consequences:**
- Shift/scheduling schema keys primarily on `user_id` with `campaign_id` as a column, not the reverse.
- Dashboard needs a "My Week" view that's campaign-agnostic while still respecting campaign isolation when drilling into a specific voter or turf.
- The relational ask ranking service queries across all campaigns the volunteer is a member of, not just one campaign's universe.
