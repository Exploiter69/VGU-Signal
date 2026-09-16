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

- [ ] Source registry.
- [ ] HTTP acquisition adapter.
- [ ] robots/sitemap policy handling.
- [ ] HTTP status/content-type validation.
- [ ] Raw content SHA-256 hashing.
- [ ] Evidence metadata storage.
- [ ] Last-Modified / ETag support where available.
- [ ] Retry/backoff and rate limiting.
- [ ] Last-known-good behavior.
- [ ] Fixture-based source tests.
- [ ] Failure observability.

**Exit gate:** the system can fetch known sources repeatedly, detect unchanged content, detect changed content, and preserve evidence without silently losing history.

## Phase 2 — Deterministic extraction and normalization

**Goal:** turn source material into structured university information.

- [ ] HTML extraction.
- [ ] PDF text extraction with PyMuPDF.
- [ ] pdfplumber fallback/cross-check.
- [ ] OCR fallback for genuinely scanned/garbled documents.
- [ ] Document metadata extraction.
- [ ] Date/deadline extraction.
- [ ] Event extraction.
- [ ] Notice classification.
- [ ] Academic calendar normalization.
- [ ] Source-relative identifiers.
- [ ] Parser versioning.
- [ ] Extraction confidence/quality signals.

**Exit gate:** structured records can be generated deterministically from fixtures and traced back to their source evidence.

## Phase 3 — Verification, deduplication and change history

**Goal:** establish the core trust layer.

- [ ] Evidence → claim model.
- [ ] Verification state machine.
- [ ] Same-content deduplication.
- [ ] URL replacement detection.
- [ ] Cross-source similarity detection.
- [ ] Supersession relationships.
- [ ] Expiration handling.
- [ ] Conflict detection.
- [ ] Correction history.
- [ ] Human-readable provenance.
- [ ] Regression tests for false positives and false negatives.

**Exit gate:** no published deadline/notice can exist without a traceable evidence chain.

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
