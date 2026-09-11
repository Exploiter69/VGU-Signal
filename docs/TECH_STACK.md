# Concrete Technical Stack

This document turns the architecture baseline into an implementation-ready stack. The stack is deliberately boring, deterministic and compatible with the project's ₹0 operating constraint.

## 1. Repository shape

VGU Signal uses a small monorepo with clear runtime boundaries:

```text
VGU-Signal/
├── src/
│   └── vgu_signal/
│       ├── domain/          # pure domain models and state transitions
│       ├── sources/         # source adapters and source registry
│       ├── acquisition/     # HTTP fetching, retries, normalization
│       ├── extraction/      # HTML/PDF/text extraction
│       ├── verification/    # claims, dedupe, conflicts, supersession
│       ├── storage/         # repository interfaces + local implementation
│       ├── notifications/   # notification decisions and idempotency
│       └── config.py
├── worker/
│   └── src/                 # Cloudflare Worker / Telegram webhook API
├── tests/
│   ├── unit/
│   ├── fixtures/
│   ├── integration/
│   └── regression/
├── migrations/              # D1-compatible SQL migrations
├── scripts/                 # local/dev maintenance utilities
├── .github/workflows/       # scheduled acquisition and CI
└── docs/
```

The Python package owns the authoritative acquisition/processing logic. The Worker remains a thin delivery/API boundary and must not duplicate verification rules.

## 2. Acquisition and processing runtime

**Python 3.12+** is the baseline runtime for local development and GitHub Actions.

Initial dependencies:

- `httpx` — ordinary HTTP acquisition with explicit timeouts.
- `beautifulsoup4` — deterministic HTML parsing.
- `pymupdf` — primary PDF text extraction.
- `pdfplumber` — fallback/cross-check for difficult PDFs.
- `pydantic` — boundary validation for parsed/configured data where useful.
- `pytest` — test runner.
- `pytest-cov` — coverage reporting.
- `ruff` — linting and formatting.
- `mypy` — static type checking.

Do not add a dependency merely because it makes a single scraper easier. Source-specific libraries require justification and fixture coverage.

## 3. Browser rendering

Browser automation is **not** an MVP dependency.

The acquisition ladder remains:

```text
robots/sitemap/API/feed
        ↓
ordinary HTTP
        ↓
HTML parser
        ↓
adaptive extraction
        ↓
browser rendering only when justified
```

If a VGU source genuinely requires rendering, the browser capability is isolated behind a source adapter. It must not become a requirement for all sources.

## 4. PDF and document processing

Primary path:

```text
PDF
 ↓
PyMuPDF
 ↓
quality check
 ↓
structured normalization
```

Fallback path:

```text
poor/ambiguous extraction
 ↓
pdfplumber cross-check
 ↓
quality check
```

OCR is an explicit fallback for scanned/image-only documents. It is not run blindly against every PDF.

## 5. Production state

Production transactional state targets **Cloudflare D1**.

Raw evidence artifacts target **Cloudflare R2** when retention is useful and within the free allowance.

The Python acquisition jobs do not directly become a long-running server. They run as scheduled GitHub Actions jobs and write through narrowly scoped interfaces.

## 6. User-facing runtime

The first channel is Telegram.

The production delivery boundary is a **Cloudflare Worker written in TypeScript**:

```text
Telegram
   ↓ webhook
Cloudflare Worker
   ↓
D1
   ↓
response / notification decision
```

The Worker should handle lightweight operations only:

- webhook validation;
- command routing;
- user preferences;
- read queries;
- notification delivery;
- links to authoritative sources.

Heavy crawling, PDF parsing and large-scale processing stay in GitHub Actions.

## 7. Local development database

SQLite is allowed for deterministic local tests and development fixtures.

It is not the production database. Production SQL must remain compatible with D1's SQLite-derived SQL model, with schema migrations tested locally before deployment.

## 8. Configuration and secrets

Configuration is environment-driven.

Never commit:

- Telegram bot tokens;
- API keys;
- credentials;
- session cookies;
- private ERP access material.

The deterministic MVP requires no paid AI credential and should not require any AI credential at all.

## 9. AI boundary

AI is optional and out of the critical path for the first implementation vertical slice.

Future AI adapters may provide:

- summaries;
- difficult document interpretation;
- semantic search;
- natural-language queries;
- community-submission matching.

AI output must reference verified evidence and can never directly change authoritative state.

## 10. Quality tooling

Every implementation change should be able to pass:

```text
ruff format --check .
ruff check .
mypy src
pytest -q
```

Integration tests that require live VGU sources are separate from the deterministic CI suite. CI must use committed fixtures for reproducibility.

## 11. Zero-cost rule

The architecture may use free hosted tiers, but no component is allowed to assume that a paid tier will be enabled later to make the design correct.

If a free-tier limit is reached, the system should degrade through scheduling/backoff/retention controls rather than silently incur charges.

Free-tier limits must be re-verified immediately before production deployment because provider quotas can change.
