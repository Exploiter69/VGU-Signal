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

**Status: COMPLETE when the Phase 1 exit gate passes on the same revision as the documentation update.**

### Objective

Reliably acquire a small, high-value set of official public VGU sources while preserving immutable evidence history and never replacing a last-known-good state with a transient failure.

### Prerequisites

Before implementation:

1. Phase 0 CI must be green on `main`.
2. The source strategy and trust model must be frozen for this gate.
3. Authenticated ERP pages, private WhatsApp groups and student credentials must remain excluded.
4. Initial sources must be public and attributable to VGU.
5. No paid API, proxy, crawler, browser service or hosted scraper may be required.
6. Every live-source decision must be representable in fixtures so CI does not depend on the live VGU site.

### Step 1 — Confirm the initial source inventory

The initial registry covers these high-value public source classes:

1. official resources / handbooks / academic-calendar index;
2. examination rules;
3. public university/CDOE notice material;
4. public fee information;
5. public events information.

Academic-calendar documents are discovered from the official resources index rather than hard-coding unstable document filenames. The index is itself an authoritative acquisition target; linked PDFs become evidence targets once discovered by the deterministic extraction layer in the next phase.

### Step 2 — Define acquisition policy

Every source must have:

- stable source ID;
- canonical URL;
- official source classification;
- allowed content types;
- robots policy behavior;
- bounded response size;
- request timeout;
- bounded retries;
- exponential retry backoff;
- `Retry-After` handling where supplied;
- minimum request interval/rate limit;
- conditional request metadata when previously observed.

The acquisition layer must fail closed on unsupported content types and policy failures.

### Step 3 — Implement HTTP acquisition

The HTTP adapter must:

- follow normal HTTP redirects;
- send an explicit identifying user agent;
- stream the response instead of assuming an unbounded body;
- enforce a maximum byte limit;
- accept only successful 2xx responses or a valid 304 conditional response;
- preserve ETag and Last-Modified values;
- send `If-None-Match` and `If-Modified-Since` on later fetches;
- retry only transient failures;
- avoid retrying permanent 4xx failures;
- expose failures as structured acquisition errors rather than publishing data.

### Step 4 — Implement robots and sitemap policy handling

Before acquiring a source:

1. request the origin's `/robots.txt` through the same bounded HTTP adapter;
2. evaluate the source URL with Python's standard robots parser;
3. fail closed when the robots document explicitly disallows the configured user agent;
4. capture sitemap declarations for future discovery;
5. parse sitemap XML deterministically when a sitemap is supplied;
6. never use sitemap discovery as permission to bypass robots rules.

Robots and sitemap behavior is tested from fixtures. CI never needs the live VGU robots file.

### Step 5 — Validate and hash evidence

For every accepted 2xx response:

- normalize the media type from `Content-Type`;
- reject unsupported media types;
- hash the exact raw response bytes with SHA-256;
- capture fetch time and final response URL;
- preserve HTTP status and content type;
- preserve ETag and Last-Modified values;
- assign a deterministic evidence ID derived from source ID + raw content hash.

The raw hash is the change-detection primitive. Later extraction hashes may be added, but they must not replace the raw evidence identity.

### Step 6 — Persist immutable evidence metadata

The evidence store must:

- append new content states;
- deduplicate an identical source/content hash;
- retain earlier evidence records;
- expose source history;
- expose the latest evidence;
- expose the last-known-good evidence;
- never overwrite an old evidence state with a new body.

D1 now has an `acquisition_runs` history table in addition to the existing immutable evidence table. Production raw bytes remain designed for R2 in the later infrastructure phase; Phase 1 proves the metadata and state semantics locally without requiring paid storage.

### Step 7 — Implement unchanged/changed behavior

The acquisition result must distinguish:

```text
first successful fetch → FETCHED
same raw hash          → UNCHANGED
new raw hash           → CHANGED
304 with prior state   → UNCHANGED
transient/permanent failure → FAILED
```

A failed fetch must return the prior evidence as `last_known_good` and must not delete or downgrade it.

### Step 8 — Failure observability

Every acquisition attempt must expose:

- source ID;
- result status;
- evidence ID when available;
- last-known-good evidence ID when available;
- error text when failed.

D1 acquisition-run records provide the durable operational history needed for later health reporting. Telegram notifications are deliberately not part of this phase.

### Step 9 — Fixture-backed tests

The Phase 1 test suite must cover:

- successful HTML acquisition;
- SHA-256 hashing;
- content-type validation;
- response-size limits;
- permanent HTTP failures;
- transient HTTP retry;
- conditional GET headers;
- 304 handling;
- robots allow/deny;
- sitemap XML parsing;
- identical-content deduplication;
- changed-content history preservation;
- last-known-good after failure;
- source registry completeness.

No Phase 1 test should require VGU's live website.

### Step 10 — Exit gate

Phase 1 is complete only when all of the following are true on one verified revision:

- [x] initial official source inventory is registered;
- [x] HTTP acquisition adapter is bounded and deterministic under test;
- [x] robots policy handling is implemented;
- [x] sitemap parsing/metadata handling is implemented;
- [x] HTTP status validation is implemented;
- [x] content-type validation is implemented;
- [x] raw SHA-256 hashing is implemented;
- [x] ETag / Last-Modified conditional requests are implemented;
- [x] retry/backoff and rate limiting are implemented;
- [x] immutable evidence metadata storage is implemented;
- [x] unchanged/changed detection is implemented;
- [x] last-known-good behavior is implemented;
- [x] acquisition failure observability is implemented;
- [x] fixture-backed Phase 1 tests pass;
- [x] full Ruff, mypy, pytest and Worker CI remains green;
- [x] roadmap and status documentation are synchronized.

The gate proves the core invariant:

> A source can fail, change or return unchanged content without silently destroying the previous evidence history.

## Phase 2 — Deterministic extraction and normalization

Phase 2 begins only after the Phase 1 gate is closed. Its prerequisites are the stable evidence IDs, source registry and raw-content history produced here.

Planned work remains the roadmap's existing HTML/PDF extraction, metadata, date/deadline, event, notice classification, normalization, parser versioning and extraction-quality signals.
