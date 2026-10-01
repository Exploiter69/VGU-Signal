# Project Status

**As of 2026-10-01**

## Current stage

**Phase 4 — Student Information Model: COMPLETE.**

Phase 0, Phase 1, Phase 2 and Phase 3 remain closed. Phase 4 adds the stable delivery-neutral information layer between verified claims and future clients.

## Phase 4 implementation

The student information model provides:

- explicit DEADLINE, EXAM, FEES, REGISTRATION, NOTICE, EVENT, HOLIDAY and CALENDAR categories;
- optional program, branch, year and semester applicability dimensions;
- conservative deterministic scope matching;
- separate importance and urgency signals;
- published, effective, expiry, deadline and event timestamps;
- primary and additional source links;
- CHANGED, SUPERSEDES and CORRECTS relationships;
- deterministic searchable InformationArchive;
- stable information item IDs;
- a verified-claim construction path that rejects unverified or evidence-missing claims;
- durable migration 0004_information_model.sql with scope, category, priority, temporal, source-link and relationship indexes.

## Phase 4 regression coverage

The deterministic suite covers:

- complete category taxonomy;
- Phase 2 notice-category mapping;
- student dimension matching and wildcard behavior;
- importance/urgency separation;
- changed-item priority;
- temporal windows and source-link retention;
- duplicate archive IDs;
- change/supersession/correction relationships;
- text/category/scope/expiry search;
- deterministic ordering;
- stable item IDs;
- rejection of unverified claims at the verified information boundary.

Tests remain fixture/generated-input based and do not require the live VGU website, paid services, OCR binaries or LLMs.

## Phase 4 exit gate

**COMPLETE.** The same verified information can now be represented once as a delivery-neutral InformationItem and consumed by future Telegram, Worker/API or web clients without duplicating business logic.

## Trust and safety invariants retained

- Official public VGU sources remain authoritative.
- Information relevance does not become information truth.
- Applicability dimensions do not prove applicability without supporting source material.
- Verification remains controlled by the Phase 3 evidence chain.
- Changed, conflicting, superseded and corrected history is retained.
- Source links remain attached to student-facing information.
- Authenticated ERP and private WhatsApp data remain out of scope.
- No paid-service dependency is introduced.

## Quality gate

The synchronized quality gate for Phase 4 is:

```text
ruff format --check .
ruff check .
mypy src
pytest -q
worker: npm install && npm run typecheck
```

## Next gate

**Phase 5 — Telegram MVP.**

## Phase 5 implementation

The Telegram MVP provides:
- Telegram Bot API webhook foundation;
- durable /start onboarding for program, branch, year, semester and categories;
- /latest, /upcoming, /search, /verify and /settings;
- source/provenance and changed/superseding/correcting state display;
- deadline reminders and weekly digest;
- durable notification deduplication;
- quiet hours, mute/unmute and per-channel toggles;
- D1-backed users, preferences, onboarding sessions and notification history.

Migration 0005_telegram_mvp.sql contains the delivery state schema.

## Phase 5 exit gate

**COMPLETE.** A student can subscribe, configure relevance preferences, receive relevant verified information, inspect the official source, and distinguish changed/superseding/correcting information from current information. Notification delivery is durable and respects user controls.

## Next gate

**Phase 6 — Production-free infrastructure.**


## Phase 6 implementation

**Phase 6 — Production-free infrastructure: COMPLETE.**

- six-hour GitHub Actions acquisition;
- deterministic extraction/verification/information generation;
- immutable R2 evidence objects;
- D1 migration `0006_operations.sql`;
- pipeline/source-health/backup operational state;
- Worker D1/R2 bindings and dependency health checks;
- secret-management contract;
- bounded retry/rate-limit policy;
- recovery procedure and free-tier guardrails.

**Next gate: Phase 7 — Verification assistant.**


## Phase 7 implementation

**Phase 7 — Verification assistant: COMPLETE.**

Implemented:
- voluntary forwarded-message intake;
- image/PDF intake and extraction;
- deterministic matching against current verified official information;
- evidence/source response;
- conflict explanation without automatic winner selection;
- explicit “Not officially confirmed” no-match response;
- durable moderator review queue.

Migration 0007_verification_assistant.sql contains submission, match and review state.

## Phase 7 exit gate

**COMPLETE.** A voluntary student submission can be checked against known official VGU evidence without turning absence of evidence into a false claim.

## Next gate

**Phase 8 — Search, calendar and quality-of-life features.**
