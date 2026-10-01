# Phase 8 — Search, Calendar and Quality-of-Life Features

**Status: COMPLETE.**

Phase 8 adds deterministic convenience features on top of the existing verified InformationItem layer. It does not change evidence, verification, or authority rules.

## Deliverables

### 1. Natural-language search
The /search command accepts ordinary questions such as:
- exam forms this week
- deadlines next week
- fees tomorrow
- holiday today

The parser is deterministic. It recognizes supported category aliases and bounded time phrases (today, tomorrow, this week, next week) and sends the remaining terms through the verified archive search. No LLM or external search service is used.

### 2. What changed
/changes shows verified CHANGED, SUPERSEDES, and CORRECTS relationships from the last 30 days, retaining the old item title where available.

### 3. Personalized this week
/week returns the user's currently applicable verified information for the current UTC Monday–Sunday window, respecting program, branch, year, semester and category preferences.

### 4. iCalendar export
/calendar creates a random, hashed, 90-day export token and returns a private .ics feed URL. The feed contains the user's applicable verified events, holidays, calendar dates and deadlines for the next 90 days. The token is stored only as a SHA-256 hash in D1 and expires automatically.

The feed is generated from current verified D1 information at request time; it is not a second copy of the evidence store.

### 5. Deadline conflict detection
/conflicts reports potential deadline collisions when verified deadlines for the user's scope occur within 24 hours of one another over the next 14 days. This is explicitly a time-proximity warning, not a claim that the university scheduled an impossible overlap.

### 6. Important-document shortcuts
/documents provides a personalized shortcut to current high/critical-importance NOTICE and CALENDAR information with the existing official source links.

### 7. Improved event/calendar views
/events provides a 30-day chronological view of verified events, holidays and calendar dates.

## Trust boundary

All Phase 8 query paths start from current VERIFIED InformationItem records and preserve the Phase 3/4 supersession and applicability filters. No Phase 8 feature creates, verifies, or publishes a claim.

Natural-language search is intentionally deterministic because semantic/LLM retrieval is deferred to Phase 9.

## Persistence

Migration 0008_phase8_calendar_exports.sql adds calendar_export_tokens with:
- SHA-256 token hash;
- owning user;
- creation and expiry timestamps;
- last-used timestamp;
- user/expiry index.

No new paid dependency is introduced.

## Quality gate

- Worker TypeScript typecheck.
- Worker Phase 8 Node test suite.
- Python Ruff format/lint.
- Python mypy.
- Python pytest.
- Existing production-pipeline syntax checks.

## Commands

/search <question>
/week
/changes
/events
/documents
/conflicts
/calendar

Existing /latest, /upcoming, /verify and all preference/trust behavior remain intact.
