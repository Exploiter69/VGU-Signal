# VGU Signal Implementation Plan

This document records the execution plan by phase. The order is deliberate: prove the deterministic evidence pipeline before building delivery, personalization or AI features.

## Phase 0 — Foundation and contracts

The Phase 0 plan established the repository, domain contracts, ports, fixture strategy, first source skeleton, verification skeleton and CI gate. Phase 0 is complete; its original architecture and quality-gate decisions remain the baseline.

### Phase 0 objective

Finish the repository foundation without prematurely building the entire product. The output is a small, testable repository skeleton that can safely absorb official VGU sources.

### Phase 0 first vertical slice

```text
Official VGU source
      ↓
source adapter
      ↓
bounded fetch
      ↓
SHA-256 evidence
      ↓
deterministic extraction
      ↓
normalized document
      ↓
verified claim candidate
      ↓
fixture-backed tests
```

### Phase 0 deliberate non-goals

- Telegram UX polish;
- broad source crawling;
- browser automation as a default;
- OCR optimization;
- AI integration;
- student personalization algorithms;
- production deployment;
- private ERP access;
- WhatsApp group ingestion.

## Phase 1 — Source Discovery & Evidence Engine

Phase 1 is complete. Its source registry, acquisition policy, bounded HTTP behavior, immutable evidence history, conditional requests, robots/sitemap handling, failure observability and fixture suite are the prerequisite boundary for Phase 2.

## Phase 2 — Deterministic extraction and normalization

**Status: COMPLETE.**

Phase 2 turns accepted Phase 1 evidence into deterministic structured candidates. Its complete extraction contract, parser implementations, fallback policy and fixture strategy are retained above as the implementation baseline.

### Phase 2 exit gate

**COMPLETE.** The deterministic extraction pipeline produces structured records from fixture evidence, retains the exact Phase 1 evidence/source provenance on every extracted document, covers HTML/PDF/pdfplumber/OCR/text dispatch and normalization paths, and passes the repository quality gate.

## Phase 3 — Verification, deduplication and change history

**Status: COMPLETE.** See `docs/PHASE3_TRUST_LAYER.md` for the detailed implementation contract.

### Objective

Turn Phase 2 candidates into an explicit trust layer without introducing a second authority. Verification is deterministic, evidence-backed and reviewable; history is preserved rather than overwritten.

### Prerequisites

1. Phase 1 evidence IDs and immutable raw evidence history are available.
2. Phase 2 extraction records retain evidence ID, source ID, document ID and source-relative identity.
3. No network access occurs inside verification.
4. No AI/LLM is used to decide verification, conflicts, supersession or publication.
5. Existing source and evidence records remain authoritative.
6. All trust behavior is deterministic and fixture-testable.

### Step 1 — Evidence → claim model

Create `EvidenceClaim` records containing document ID, evidence ID, source ID, statement, normalized statement, SHA-256 fingerprint, verification state, observation timestamps and optional effective/supersession/correction references. Claim creation always starts `UNVERIFIED`.

### Step 2 — Verification state machine

Allow only explicit legal transitions between `UNVERIFIED`, `VERIFIED`, `CONFLICTING`, `SUPERSEDED`, `EXPIRED` and `REMOVED`. Illegal transitions fail closed. Superseded and removed states cannot silently be resurrected.

### Step 3 — Same-content deduplication

Normalize statements deterministically and use SHA-256 fingerprints for exact-content identity. Deduplication never deletes or mutates underlying evidence history.

### Step 4 — URL replacement detection

Treat a changed URL as a replacement only when the source ID and source-relative logical identifier remain identical. Different logical identities are not merged merely because titles or URLs look similar.

### Step 5 — Cross-source similarity

Use deterministic token-set similarity to identify likely repeated material across different sources. Record `SIMILAR`; do not automatically merge, verify or publish it.

### Step 6 — Supersession relationships

Represent a newer claim replacing an older operational state with an explicit `SUPERSEDES` relationship and preserve the older claim in history.

### Step 7 — Expiration handling

Use explicit `effective_until` timestamps. At or after expiry, a claim resolves to `EXPIRED`; expiration does not create verification or delete evidence.

### Step 8 — Conflict detection

Conservatively flag high-overlap, different same-source claims as `CONFLICTS`. Record the relationship for review rather than selecting an automatic winner. Different-source disagreement remains similarity/review material.

### Step 9 — Correction history

Represent corrections with `CORRECTS` relationships and retain both original and correcting claims. Correction is historical state, not destructive replacement.

### Step 10 — Human-readable provenance

Expose claim → document → evidence → source URL, together with evidence hash, observation/effective timestamps and supersession/correction references. The exact evidence identity remains the audit anchor.

### Step 11 — Publication guard

Use one deterministic `publishable` guard requiring both `VERIFIED` state and presence of the referenced evidence ID. Unverified, conflicting, superseded, expired or evidence-missing claims cannot pass the guard.

### Step 12 — Durable schema

Migration `0003_trust_layer.sql` adds documents, claims, claim/evidence links, claim relationships, verification decisions and correction history with foreign keys and lookup indexes.

### Step 13 — Regression strategy

Test both false-positive and false-negative boundaries for deduplication, similarity, conflicts and URL replacement. Test missing evidence, illegal state transitions, expiration, supersession/correction, provenance and publication blocking. Tests require no live VGU network, paid service, OCR binary or LLM.

### Step 14 — Phase 3 exit gate

Phase 3 is closed only when one verified revision demonstrates:

- [x] Evidence → claim model.
- [x] Verification state machine.
- [x] Same-content deduplication.
- [x] URL replacement detection.
- [x] Cross-source similarity detection.
- [x] Supersession relationships.
- [x] Expiration handling.
- [x] Conflict detection.
- [x] Correction history.
- [x] Human-readable provenance.
- [x] Regression tests for false positives and false negatives.
- [x] Publication requires an explicit verified state and traceable evidence.
- [x] Durable trust-layer schema added.
- [x] Full Ruff format/lint, mypy and pytest pass.
- [x] Worker typecheck remains green.
- [x] Roadmap, status, implementation plan and trust-layer documentation are synchronized.

The core invariant is:

> A structured candidate is not authority. Publication requires an explicit verification state and an intact evidence chain, while every prior state remains auditable.

## Phase 4 and later

Phase 4 begins from verified Phase 3 claims and provides the stable student-information model without reimplementing evidence, verification, deduplication or history logic. Phases 4–10 otherwise remain governed by `ROADMAP.md`.
## Phase 4 — Student information model

**Status: COMPLETE.** See `docs/PHASE4_STUDENT_INFORMATION.md` for the detailed contract.

### Objective

Project verified Phase 3 claims into one stable information representation that is independent of Telegram, Worker/API or any future delivery client.

### Step 1 — Stable category taxonomy

Implement explicit categories for:

- DEADLINE
- EXAM
- FEES
- REGISTRATION
- NOTICE
- EVENT
- HOLIDAY
- CALENDAR

Map existing Phase 2 notice categories deterministically into the stable taxonomy.

### Step 2 — Student applicability dimensions

Implement optional program, branch, year and semester dimensions. Scope matching treats missing dimensions as broader applicability while incompatible known dimensions do not match.

Applicability never overrides the Phase 3 trust boundary.

### Step 3 — Importance and urgency

Keep relevance separate from truth:

- Importance: LOW / NORMAL / HIGH / CRITICAL.
- Urgency: NONE / UPCOMING / SOON / IMMEDIATE / OVERDUE.

Derive them deterministically from time proximity, category, explicit urgency wording, changed/superseding state and scope specificity.

### Step 4 — Temporal model

Preserve published_at, effective_from, effective_until, due_at, starts_at and ends_at. Effective windows are deterministic and half-open.

### Step 5 — Source links

Retain a primary authoritative source URL plus additional source links. The Phase 3 evidence/provenance chain remains the audit authority.

### Step 6 — Change and supersession

Represent CHANGED, SUPERSEDES and CORRECTS relationships without overwriting prior information.

### Step 7 — Searchable archive

Provide a delivery-neutral archive with deterministic free-text, category, scope and effective-time filtering, including an explicit option to include expired records.

### Step 8 — Verified-claim boundary

Information items are built through a verified-claim path that rejects claims unless Phase 3 publication requirements are satisfied.

### Step 9 — Durable schema

Migration `0004_information_model.sql` adds information items, student dimensions, priority/temporal fields, source links and historical relationships with lookup indexes.

### Step 10 — Regression strategy

Tests cover the complete Phase 4 contract: all categories, category mapping, scope matching, importance/urgency separation, changed-item priority, temporal fields, source links, historical relationships, duplicate IDs, search filtering/expiry, deterministic ordering, stable IDs and rejection of unverified claims.

### Phase 4 exit gate

Phase 4 is closed only when one verified revision demonstrates:

- [x] All roadmap categories are explicit.
- [x] Program/branch/year/semester dimensions are represented and queryable.
- [x] Importance and urgency are separate deterministic signals.
- [x] Published/effective/expiry and deadline/event timestamps are preserved.
- [x] Primary and additional source links are preserved.
- [x] Change/supersession/correction relationships are explicit.
- [x] The archive is searchable without delivery-specific logic.
- [x] Unverified claims cannot enter the information layer through the verified path.
- [x] Durable information schema and indexes are added.
- [x] Full Ruff format/lint, mypy and pytest pass.
- [x] Worker typecheck remains green.
- [x] Roadmap, status, data model and Phase 4 contract are synchronized.

The core invariant is:

> One verified fact becomes one delivery-neutral information item; clients render it rather than recreating its business rules.

## Phase 5 — Telegram MVP

**Status: COMPLETE.** See docs/PHASE5_TELEGRAM_MVP.md.

### Step 1 — Telegram foundation
- [x] Worker Telegram webhook handler.
- [x] Telegram API adapter.
- [x] Private-chat boundary.
- [x] Secret-token webhook validation.
- [x] Worker health endpoint.

### Step 2 — Onboarding and preferences
- [x] Durable /start flow.
- [x] Program/branch/year/semester capture.
- [x] Category capture.
- [x] Durable session state.
- [x] /settings display.
- [x] Preference mutation commands.

### Step 3 — Student query commands
- [x] /latest.
- [x] /upcoming.
- [x] /search.
- [x] Conservative /verify.
- [x] Source/provenance display.
- [x] Changed/superseding/correcting state display.

### Step 4 — Notifications
- [x] Deadline reminders.
- [x] Weekly digest.
- [x] Durable notification identity.
- [x] Retry of failed sends.
- [x] Quiet-hour filtering.
- [x] Global mute/unmute.
- [x] Per-channel reminder/digest toggles.

### Step 5 — Durable delivery schema
- [x] Users.
- [x] Preferences.
- [x] Onboarding sessions.
- [x] Notification history/deduplication.

### Step 6 — Quality and trust
- [x] No delivery path publishes unverified claims.
- [x] No-match verification response is explicitly non-falsifying.
- [x] No private/ERP ingestion.
- [x] No bot secret committed.
- [x] Python quality gate retained.
- [x] Worker typecheck retained.

### Phase 5 exit gate

**COMPLETE.**

A student can subscribe, configure relevance preferences, receive a relevant verified update, inspect its official source, and distinguish changed/superseding/correcting information from current information. Notification delivery is durable and respects mute/quiet/category preferences.


## Phase 6 — Production-free infrastructure

**Status: COMPLETE.** See `docs/PHASE6_PRODUCTION_FREE_INFRASTRUCTURE.md`.

### Step 1 — Scheduled acquisition
- [x] GitHub Actions scheduled pipeline.
- [x] Manual dispatch.
- [x] Bounded timeout/size/retry/rate-limit behavior.
- [x] Deterministic extraction and verification.
- [x] Run artifacts and manifest.

### Step 2 — Durable infrastructure state
- [x] D1 operational migration.
- [x] Pipeline run history.
- [x] Source health model.
- [x] Backup manifest model.

### Step 3 — Evidence storage
- [x] Private R2 binding.
- [x] Content-addressed evidence keys.
- [x] No public evidence endpoint.

### Step 4 — Worker deployment boundary
- [x] D1 binding.
- [x] R2 binding.
- [x] 15-minute notification schedule.
- [x] D1/R2 health endpoint.
- [x] Secret-management contract.

### Step 5 — Failure/recovery
- [x] Retry transient acquisition failures.
- [x] Preserve successful evidence on partial outages.
- [x] Idempotent evidence/information writes.
- [x] Migration-replay recovery.
- [x] Run artifact retention.

### Step 6 — Free-tier quality gate
- [x] No paid dependency.
- [x] Current free-tier limits documented.
- [x] D1 exhaustion treated as degradation, not paid fallback.
- [x] Python/Worker CI gate retained.

### Phase 6 exit gate

**COMPLETE.**


## Phase 7 — Verification assistant

**Status: COMPLETE.** See docs/PHASE7_VERIFICATION_ASSISTANT.md.

### Step 1 — Voluntary intake
- [x] Forwarded text intake.
- [x] Image/PDF intake.
- [x] Private-chat boundary.
- [x] Submission size bound.

### Step 2 — Extraction
- [x] PDF extraction through the existing deterministic extraction pipeline.
- [x] OCR fallback for PDFs.
- [x] Tesseract image OCR on the free GitHub runner.
- [x] Extracted-text size bound.

### Step 3 — Official matching
- [x] Current VERIFIED information only.
- [x] Deterministic content comparison.
- [x] Date comparison.
- [x] Stable match ordering.
- [x] Official source links in responses.

### Step 4 — Trust responses
- [x] Official evidence match.
- [x] Conflict explanation.
- [x] Not officially confirmed response.
- [x] No automatic false verdict.
- [x] No automatic conflict winner.

### Step 5 — Review and durability
- [x] Durable submission state.
- [x] Match history.
- [x] Moderator review queue.
- [x] Response-delivery state.
- [x] 15-minute processing workflow.

### Phase 7 exit gate

**COMPLETE.**


## Phase 8 — Search, calendar and quality-of-life features

**Status: COMPLETE.** See docs/PHASE8_SEARCH_CALENDAR_QOL.md.

### Exit-gate checklist
- [x] Natural-language search over verified information.
- [x] “What changed?” timeline.
- [x] Personalized “this week” view.
- [x] `.ics` calendar export.
- [x] Deadline conflict detection.
- [x] Important-document shortcuts.
- [x] Improved event/calendar views.
- [x] Deterministic Worker tests cover search intent, week ranges, deadline collision grouping and iCalendar generation.
- [x] Calendar export tokens are hashed, scoped to a user and expiring.
- [x] No Phase 8 path bypasses the VERIFIED InformationItem boundary.
- [x] No paid dependency introduced.
- [x] Roadmap, status and Phase 8 contract synchronized.

### Phase 8 trust invariant

> Convenience features render the same verified information model; they do not create a second authority or infer truth from user language.
