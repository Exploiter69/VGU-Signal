# VGU Signal Roadmap

This roadmap is the execution plan for VGU Signal. The order is deliberate: **trust and reliability before convenience, automation and AI**.

## Principles

1. Official sources remain authoritative.
2. Every published fact must be traceable to evidence.
3. A changed document is a new state, not an overwritten history.
4. AI may assist interpretation but never becomes the authority.
5. Authenticated student systems are not scraped without explicit authorization.
6. Private WhatsApp groups and private student data are out of scope.
7. Core operation must remain possible at ₹0 / $0.
8. Prefer deterministic components and simple failure modes.
9. Ship vertical slices that can be tested end-to-end.
10. Never trade correctness for feature count.

## Phase 0 — Foundation and contracts

**Goal:** establish the repository and engineering contracts before production code.

- [x] Repository created.
- [x] Product thesis documented.
- [x] Architecture documented.
- [x] Trust model documented.
- [x] Source strategy documented.
- [x] Product scope and non-goals documented.
- [x] Privacy and security boundaries documented.
- [x] Select implementation stack.
- [x] Add project configuration and quality-gate specification.
- [x] Add implementation plan and fixture/test strategy.
- [x] Repository bootstrap implemented.
- [x] Domain, acquisition, extraction and source-registry skeleton implemented.
- [x] D1 migration foundation implemented.
- [x] Fixture-backed test foundation implemented.
- [x] Final Ruff format check passed.
- [x] Final Ruff lint check passed.
- [x] Final mypy check passed.
- [x] Final pytest suite passed.
- [x] Final Worker typecheck passed.

**Concrete stack:** Python 3.12+, `httpx`, BeautifulSoup, PyMuPDF, pdfplumber, Pydantic where useful, pytest, Ruff and mypy; TypeScript Cloudflare Worker for the delivery boundary; D1/R2 for production state/evidence; GitHub Actions for scheduled acquisition.

**Execution plan:** see `docs/IMPLEMENTATION_PLAN.md`, `docs/TECH_STACK.md` and `docs/QUALITY_GATES.md`.

**Exit gate:** COMPLETE. The repository foundation, contracts, deterministic skeleton, fixture/test foundation and CI quality gates are implemented and the full deterministic CI suite passed on the Phase 0 verification revision.

## Phase 1 — Source discovery and evidence engine

**Goal:** reliably acquire a small, high-value set of official public VGU sources.

Initial source classes:

1. VGU official resources/handbooks page.
2. Academic calendar documents.
3. Examination rules and examination-cell public notices.
4. Public university notices.
5. Public fee-related information.
6. Public events information.

Work:

- [x] Source registry.
- [x] HTTP acquisition adapter.
- [x] robots/sitemap policy handling.
- [x] HTTP status/content-type validation.
- [x] Raw content SHA-256 hashing.
- [x] Evidence metadata storage.
- [x] Last-Modified / ETag support where available.
- [x] Retry/backoff and rate limiting.
- [x] Last-known-good behavior.
- [x] Fixture-based source tests.
- [x] Failure observability.

**Phase 1 implementation notes:** the official resources index is the initial discovery anchor for academic calendars and related documents; examination rules, public notice, fee and event pages/documents are explicitly registered. Conditional requests are opportunistic, with SHA-256 as the fallback change detector. Robots restrictions are honored and sitemap declarations are discovery metadata only. Failed acquisition leaves last-known-good evidence intact.

**Exit gate:** COMPLETE. The deterministic acquisition layer can repeatedly fetch known sources under bounded HTTP behavior, detect unchanged and changed content, preserve immutable evidence history, honor robots policy, retain validators, retry transient failures and preserve last-known-good state after failures. The complete fixture-backed Phase 1 suite and the repository CI quality gate pass on the verification revision.

## Phase 2 — Deterministic extraction and normalization

**Goal:** turn source material into structured university information.

- [x] HTML extraction.
- [x] PDF text extraction with PyMuPDF.
- [x] pdfplumber fallback/cross-check.
- [x] OCR fallback for genuinely scanned/garbled documents.
- [x] Document metadata extraction.
- [x] Date/deadline extraction.
- [x] Event extraction.
- [x] Notice classification.
- [x] Academic calendar normalization.
- [x] Source-relative identifiers.
- [x] Parser versioning.
- [x] Extraction confidence/quality signals.

**Phase 2 implementation notes:** extraction consumes Phase 1 evidence bytes directly and never fetches live URLs. HTML parsing is deterministic and non-executing; PDF extraction is PyMuPDF-first with pdfplumber fallback/cross-check; sparse PDF text may fall back to locally invoked tesseract after deterministic page rendering. Dates, deadlines, events, classification and calendar rows are explicit deterministic candidates only. Source-relative identifiers are scoped by source and canonical URL. Parser versions are recorded in extracted documents, and quality records score, level, extraction kind, text length, page count and warnings. Unsupported media types fail closed. Fixtures cover primary, fallback, OCR, metadata, normalization, idempotency and failure paths without the live VGU website or paid services.

**Exit gate:** COMPLETE. The deterministic extraction pipeline produces structured records from fixture evidence, retains the exact Phase 1 evidence/source provenance on every extracted document, covers HTML/PDF/pdfplumber/OCR/text dispatch and normalization paths, and passes the repository quality gate on the same synchronized revision.

## Phase 3 — Verification, deduplication and change history

**Goal:** establish the core trust layer.

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

**Phase 3 implementation notes:** Phase 3 consumes Phase 2 records without performing network access. Claims retain document/evidence/source identity and deterministic fingerprints. Verification is explicit and state transitions are constrained. Same-content deduplication is fingerprint-based; URL replacement requires the same source-relative logical identity; cross-source overlap is recorded as similarity rather than automatically merged. Same-source high-overlap differences are surfaced as conflicts for review rather than assigning a winner. Supersession and correction remain explicit historical relationships. Effective intervals support deterministic expiration. Publication is guarded by verified state plus evidence presence. The durable trust-layer migration preserves documents, claims, evidence links, relationships, verification decisions and correction history.

**Exit gate:** COMPLETE. Fixture-backed tests prove that only evidence-backed verified claims are publishable, historical relationships remain explicit, conflicting/changed material is not silently selected as authoritative, and provenance remains traceable to the exact Phase 1 evidence.

## Phase 4 — Student information model

**Goal:** provide a stable internal model independent of delivery channel.

- [ ] Categories: deadlines, exams, fees, registration, notices, events, holidays, calendar.
- [ ] Program/branch/year/semester dimensions.
- [ ] Importance and urgency model.
- [ ] Effective/published/expiry timestamps.
- [ ] Source links.
- [ ] Change and supersession relationships.
- [ ] Searchable archive.

**Exit gate:** the same verified information can be rendered for different clients without duplicating business logic.

## Phase 5 — Telegram MVP

**Goal:** deliver trustworthy information to students.

- [ ] Telegram bot foundation.
- [ ] `/start` onboarding.
- [ ] Program/branch/year/semester preferences.
- [ ] Category preferences.
- [ ] `/latest`.
- [ ] `/upcoming`.
- [ ] `/search`.
- [ ] `/verify`.
- [ ] `/settings`.
- [ ] Source/provenance display.
- [ ] Deadline reminders.
- [ ] Weekly digest.
- [ ] Notification deduplication.
- [ ] Quiet/mute controls.

**Exit gate:** a student can subscribe, receive a relevant verified update, inspect its source, and distinguish a changed/superseded item from a current one.

## Phase 6 — Production-free infrastructure

**Goal:** operate reliably without paid services.

Target architecture:

```text
VGU public sources
      ↓
GitHub Actions
(fetch / parse / OCR / hash)
      ↓
Cloudflare R2 ← raw evidence artifacts
      ↓
Cloudflare D1 ← live application state
      ↓
Cloudflare Worker ← webhook/API
      ↓
Telegram
```

- [ ] GitHub Actions scheduled pipeline.
- [ ] D1 schema and migrations.
- [ ] R2 evidence storage policy.
- [ ] Worker webhook/API.
- [ ] Secret management.
- [ ] Rate-limit safeguards.
- [ ] Failure/retry strategy.
- [ ] Operational health checks.
- [ ] Backup/recovery procedure.

Free-tier limits must be rechecked before deployment and monitored in production. No paid-tier assumption may be hidden in code or documentation.

## Phase 7 — Verification assistant

**Goal:** answer “Is this VGU notice real?” without becoming a rumor engine.

Flow:

```text
student submission
      ↓
extract text / metadata
      ↓
search known official evidence
      ↓
compare content + dates + identifiers
      ↓
OFFICIAL VERIFIED / CONFLICTING / UNVERIFIED
```

- [ ] Voluntary forwarded-message intake.
- [ ] Image/PDF text extraction.
- [ ] Official-source matching.
- [ ] Evidence response.
- [ ] Conflict explanation.
- [ ] “Not officially confirmed” response.
- [ ] Moderator review queue where needed.

**Hard rule:** absence of an official match does not prove that a claim is false. The system must say that it is unverified unless evidence supports a stronger conclusion.

## Phase 8 — Search, calendar and quality-of-life features

- [ ] Natural-language search over verified information.
- [ ] “What changed?” timeline.
- [ ] Personalized “this week” view.
- [ ] `.ics` calendar export.
- [ ] Deadline conflict detection.
- [ ] Important-document shortcuts.
- [ ] Improved event/calendar views.

## Phase 9 — AI augmentation

Only after the deterministic core is reliable.

- [ ] Optional local LLM gateway.
- [ ] Source-grounded summaries.
- [ ] Difficult document explanation.
- [ ] Semantic retrieval.
- [ ] Natural-language queries.
- [ ] Community submission matching.
- [ ] AI evaluation suite.
- [ ] Hallucination/grounding tests.

AI outputs must always retain links to the verified evidence they summarize.

## Phase 10 — Expansion

Potential later sources:

- CDOE.
- Online VGU.
- Department-level public pages.
- Scholarships.
- Hostel information.
- Additional official public social accounts.
- Other public university systems.

Authenticated ERP integration is a separate track and requires explicit authorization and a legitimate official integration mechanism.

## Explicitly deferred

- Private WhatsApp scraping.
- Student ERP credential collection.
- Authenticated ERP scraping.
- Autonomous rumor publishing.
- AI-generated deadlines without evidence.
- Universal web crawling.
- Paid infrastructure as a required dependency.
- Feature-heavy mobile apps before the information pipeline is reliable.

## Release philosophy

A release is ready only when its trust contract is stronger than the previous release. A feature that increases the chance of publishing wrong university information is not worth shipping merely because it is impressive.
