# Project Status

**As of 2026-09-17**

## Current stage

**Phase 2 — Deterministic Extraction & Normalization: COMPLETE.**

Phase 0 and Phase 1 remain closed and unchanged. Phase 2 now converts accepted Phase 1 evidence bytes into deterministic structured extraction results without fetching live URLs, bypassing acquisition policy, or treating extraction output as verified authority.

## Phase 2 implementation

The extraction boundary is evidence-first and fail-closed:

- HTML is parsed with BeautifulSoup without executing page scripts;
- `main`/`body` content is selected deterministically and normalized;
- relative links are resolved against the evidence URL and deduplicated in first-seen order;
- HTML metadata and explicit machine-readable publication timestamps are retained;
- PDFs are extracted page-by-page with PyMuPDF;
- pdfplumber provides fallback/cross-check behavior and disagreements are surfaced as warnings;
- sparse PDF text can fall back to locally invoked tesseract after deterministic PyMuPDF page rendering;
- OCR failure or unavailable OCR preserves the sparse extraction and records a quality warning;
- PDF metadata and page count are retained;
- supported explicit date forms are parsed and invalid dates are rejected;
- deadline candidates require explicit deadline/submission language plus an explicit date;
- event candidates require event language plus an explicit date;
- notice classification is deterministic across ACADEMIC, EXAMINATION, FEES, REGISTRATION, EVENT, HOLIDAY, GENERAL and UNKNOWN;
- academic-calendar rows retain source text, explicit date ranges, stable source-relative IDs, deterministic ordering and confidence;
- source-relative identifiers are scoped by source ID, canonical URL and stable key;
- parser versions are recorded and included in document identity;
- extraction quality records score, level, text length, page count, extraction kind and warnings;
- unsupported media types fail closed;
- every extracted document retains evidence ID, source ID and canonical source URL.

## Phase 2 fixture coverage

The deterministic suite covers:

- supported date forms and invalid dates;
- positive and negative deadline extraction;
- positive and negative event extraction;
- every notice classification category plus UNKNOWN;
- source-relative identifier stability and source scoping;
- PyMuPDF PDF extraction, metadata and quality;
- pdfplumber cross-check disagreement;
- pdfplumber fallback after primary extraction failure;
- sparse-PDF OCR fallback and parser-kind recording;
- OCR failure without fabricated text;
- HTML metadata, publication time, relative links, duplicate-link removal and executable-node removal;
- HTML/PDF/TEXT dispatcher routing;
- unsupported-media fail-closed behavior;
- calendar date ranges, single dates, duplicates, missing-date rows and deterministic ordering;
- repeated extraction idempotency and provenance retention.

All tests are fixture/generated-input based and do not require the live VGU website, paid services or a preinstalled OCR binary.

## Phase 2 exit gate

**COMPLETE.** The exit gate is satisfied by the deterministic extraction implementation and its fixture-backed regression coverage. The final repository quality gate must remain green on the synchronized revision:

```text
ruff format --check .
ruff check .
mypy src
pytest -q
worker: npm install && npm run typecheck
```

The core invariant remains:

> Extraction may produce structured candidates, but it may never manufacture authority. Every extracted record remains tied to the exact Phase 1 evidence that produced it.

## Trust and safety invariants retained

- Official public VGU sources remain authoritative.
- Evidence identity is based on exact raw bytes, not an AI interpretation.
- Discovery does not equal publication or verification.
- Robots restrictions are honored rather than bypassed.
- Authenticated ERP and private WhatsApp data remain out of scope.
- No paid-service dependency is introduced by Phase 2.
- Live website availability is not required for CI.
- OCR is local-only and optional; it cannot invent replacement text on failure.
- Unsupported media types cannot silently enter the structured-information pipeline.

## Phase 3 readiness

**Phase 3 is now the next gate.** Its prerequisites are satisfied: stable Phase 1 evidence IDs, deterministic Phase 2 document records, provenance retention, parser versioning, quality signals and fixture-backed extraction behavior. Phase 3 may now consume these records for evidence-to-claim verification, deduplication, conflict handling, supersession and correction history.
