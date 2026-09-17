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

**Status: COMPLETE when the Phase 2 exit gate passes on the same revision as the roadmap/status synchronization.**

### Objective

Turn accepted Phase 1 evidence into deterministic, structured university information without bypassing the evidence layer and without allowing extraction guesses to become facts.

### Prerequisites

Before implementation:

1. Phase 1 must be closed on `main` with stable source IDs and evidence IDs.
2. Raw evidence history and last-known-good semantics must remain immutable.
3. Extraction must accept evidence bytes plus their provenance; it must never fetch the live URL itself.
4. Existing `httpx` acquisition behavior remains the only network boundary.
5. HTML parsing uses BeautifulSoup; no browser automation is required for this phase.
6. PDF extraction uses PyMuPDF first and pdfplumber as fallback/cross-check.
7. OCR is optional and local-only through the tesseract CLI; no hosted OCR/API is permitted.
8. Every fixture must be deterministic and runnable without the live VGU website.
9. Unsupported content types fail closed.
10. No AI/LLM is used for extraction, date interpretation, classification or calendar normalization.

### Step 1 — Define the extraction contract

Each extracted document carries:

- stable document ID;
- Phase 1 evidence ID;
- source ID;
- canonical source URL;
- title;
- published timestamp when explicitly available;
- normalized body text;
- resolved source links;
- parser version;
- extraction kind (`HTML`, `PDF`, `OCR`, `TEXT`);
- deterministic metadata;
- extracted dates;
- extracted deadlines;
- extracted events;
- notice category;
- source-relative identifier;
- extraction quality score/level, text length, page count and warnings.

The extraction model is intentionally separate from the later verified claim model. Extraction output is evidence-derived input, not publication authority.

### Step 2 — HTML extraction

For HTML evidence:

1. parse bytes with BeautifulSoup;
2. remove executable/non-content `script`, `style`, `noscript` and `template` nodes;
3. prefer `<main>`, then `<body>`, then the document root;
4. normalize whitespace while preserving meaningful line boundaries;
5. extract the `<title>` with a deterministic fallback;
6. resolve relative links with the evidence URL;
7. deduplicate links while preserving first-seen order;
8. collect standard metadata tags (`name` and `property`);
9. parse an explicit publication timestamp only when it is machine-readable;
10. derive dates/deadlines/events/classification from extracted text.

No page is rendered or executed. Client-side content that is absent from the acquired HTML remains absent rather than guessed.

### Step 3 — PDF primary extraction

For PDF evidence:

1. open bytes with PyMuPDF;
2. extract text page-by-page in document order;
3. collect PDF metadata;
4. normalize extracted text;
5. preserve page count;
6. calculate quality from extracted text volume;
7. run pdfplumber as a deterministic cross-check;
8. use the longer extraction only when it is clearly more complete;
9. record a warning whenever the two extractors disagree;
10. retain the original evidence ID regardless of extraction result.

Parser versions are explicit so future parser changes cannot silently reinterpret historical evidence as though an older parser produced the new result.

### Step 4 — OCR fallback

OCR is only attempted when ordinary PDF extraction remains genuinely sparse (fewer than 100 normalized characters).

1. render each PDF page deterministically with PyMuPDF at a fixed DPI;
2. invoke the locally installed `tesseract` CLI on PNG page bytes;
3. combine page results in original order;
4. normalize the OCR text;
5. switch extraction kind to `OCR` and record the OCR parser version;
6. if tesseract is unavailable, times out, or fails, retain the sparse result and emit a quality warning;
7. never invent replacement text when OCR fails.

OCR is a fallback, not a new authority. CI tests the fallback path by fixture and mocking the local OCR boundary where necessary; CI does not require tesseract to be installed.

### Step 5 — Document metadata

Metadata must be structured and deterministic:

- HTML title and standard meta name/property pairs;
- explicit machine-readable publication time when available;
- PDF title/author/subject/keywords/creator/producer and other non-empty PyMuPDF metadata;
- page count for PDFs;
- canonical URL and source ID from Phase 1;
- evidence ID and raw-content-derived document identity.

Metadata that cannot be parsed is retained as absent, not inferred.

### Step 6 — Date and deadline extraction

Date extraction recognizes explicit, valid dates in the supported forms:

- `DD Month YYYY`;
- `DD Mon YYYY`;
- numeric `DD/MM/YYYY`, `DD-MM-YYYY` and `DD.MM.YYYY` forms;
- ISO `YYYY-MM-DD`.

Invalid calendar dates are rejected. Duplicate date observations are removed deterministically.

Deadline extraction is deliberately stricter: a date is considered a deadline candidate only when the surrounding sentence contains explicit deadline/submission language such as `deadline`, `due`, `last date`, `closing date`, `closes`, `submit by` or `submission`. The source sentence is retained with the candidate and a deterministic confidence signal. No missing time, date or timezone is guessed.

### Step 7 — Event extraction

Event candidates require both:

- event language (`event`, `seminar`, `workshop`, `webinar`, `orientation`, `fest`, `conference`, `ceremony`); and
- an explicit date in the same source sentence/row.

The first explicit date becomes the start date. An end date is not inferred unless a later normalization layer has an explicit second date. The original sentence remains attached as evidence text.

### Step 8 — Notice classification

Classification is deterministic keyword scoring across title and normalized body text. Initial categories are:

- ACADEMIC;
- EXAMINATION;
- FEES;
- REGISTRATION;
- EVENT;
- HOLIDAY;
- GENERAL;
- UNKNOWN.

When no category has a positive score, the result is `UNKNOWN`. This avoids forcing ambiguous documents into a student-facing category. Classification is an extraction signal, not verification.

### Step 9 — Academic calendar normalization

Calendar normalization consumes already extracted text rather than scraping a second source.

For each explicit calendar row/line:

1. locate one or more explicit dates;
2. use the first as start and second as end when present;
3. preserve the complete original row as `source_text`;
4. derive a stable label from the row without inventing missing values;
5. generate a source-relative deterministic ID from source, URL and normalized row identity;
6. sort normalized entries by date, label and ID;
7. deduplicate identical normalized entries;
8. emit lower confidence for single-date rows than explicit date ranges.

No semester, program, holiday meaning or missing date is guessed from context. Those semantics belong to later verification/student-model phases.

### Step 10 — Source-relative identifiers

IDs must remain scoped to the source. The identifier input includes:

```text
source_id + canonical_url + stable_key
```

The stable key is derived from deterministic evidence content or an explicit normalized row key. The same input must produce the same ID; changing the source scope must produce a different ID. These identifiers are not substitutes for Phase 1 evidence IDs.

### Step 11 — Parser versioning

Every extracted document records a parser version. Parser versions are constants in code and change when extraction semantics change materially. Document IDs include the parser version so historical extraction results are not silently conflated across parser revisions.

### Step 12 — Extraction confidence and quality

Quality is explicit and machine-readable:

- `HIGH`: substantial text extraction;
- `MEDIUM`: usable but incomplete/small extraction;
- `LOW`: sparse extraction;
- `FAILED`: no usable text.

Each result records a normalized score, text length, page count when applicable, extraction kind and warnings. Quality warnings cover extractor disagreement, failed fallbacks and unavailable OCR. Quality never upgrades an unsupported or unverified record into a verified claim.

### Step 13 — Dispatcher and fail-closed behavior

The extraction dispatcher selects the parser from normalized media type:

```text
text/html, application/xhtml+xml → HTML
application/pdf                  → PDF → optional OCR
text/plain, application/xml      → deterministic text
unsupported media                → ERROR
```

The dispatcher does not perform network access. It accepts the Phase 1 evidence body directly.

### Step 14 — Fixture strategy

The Phase 2 fixtures cover:

- HTML with navigation, scripts, styles, relative links, metadata and dates;
- valid/invalid date strings;
- deadline language with positive and negative examples;
- event language with positive and negative examples;
- each notice classification category plus UNKNOWN;
- a generated text PDF with metadata and extractable content;
- PDF extraction quality and parser version;
- sparse-PDF/OCR fallback behavior;
- source-relative ID stability and source scoping;
- calendar rows, date ranges, duplicates and deterministic ordering;
- dispatcher routing and unsupported-media fail-closed behavior.

Tests must run without VGU network access, paid services or a preinstalled OCR binary.

### Step 15 — Phase 2 exit gate

Phase 2 is closed only when one verified revision demonstrates:

- [x] HTML extraction;
- [x] PDF text extraction with PyMuPDF;
- [x] pdfplumber fallback/cross-check;
- [x] OCR fallback for sparse/scanned material;
- [x] document metadata extraction;
- [x] date/deadline extraction;
- [x] event extraction;
- [x] notice classification;
- [x] academic-calendar normalization;
- [x] source-relative identifiers;
- [x] parser versioning;
- [x] extraction confidence/quality signals;
- [x] evidence/source provenance retained on every extracted record;
- [x] deterministic fixture coverage for all paths;
- [x] unsupported media types fail closed;
- [x] full Ruff format/lint, mypy and pytest pass;
- [x] Worker typecheck remains green;
- [x] roadmap, status, implementation plan and quality gate documentation are synchronized.

The core invariant is:

> Extraction may produce structured candidates, but it may never manufacture authority. Every extracted record remains tied to the exact Phase 1 evidence that produced it.

## Phase 3 and later

Phases 3–10 remain unchanged from the roadmap. Phase 3 begins only after this extraction gate is closed and consumes these deterministic records for verification, deduplication, conflict handling and change history.
