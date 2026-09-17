# Implementation Quality Gates

VGU Signal is implemented by vertical slices, not by building a large crawler and hoping the trust model works later.

## Gate 0 — Repository bootstrap

Must pass before source implementation:

- concrete stack documented;
- Python package imports cleanly;
- Worker package has a reproducible install/build;
- lint/format/type/test commands are defined;
- CI workflow runs the deterministic checks;
- no secrets or credentials are committed.

## Gate 1 — Source + evidence vertical slice

One official VGU source must be processed end-to-end:

```text
source registry
 → fetch
 → raw hash
 → evidence record
 → parse
 → normalized document
```

Required properties:

- bounded timeout;
- explicit HTTP status handling;
- deterministic hashing;
- provenance retained;
- parser version recorded;
- fixture reproduces the parse without network access;
- failure does not delete last-known-good evidence.

## Gate 1A — Deterministic extraction and normalization

Phase 2 closes only when fixture-backed tests prove all extraction paths and quality safeguards:

- HTML is parsed without executing scripts/styles/templates;
- relative links resolve against the source URL and duplicate links are removed;
- HTML metadata and published timestamps are retained when parseable;
- PDF text is extracted primarily with PyMuPDF;
- pdfplumber is used as fallback/cross-check and disagreements are surfaced as warnings;
- sparse or scanned PDFs may use the local tesseract CLI after deterministic page rendering;
- missing OCR tooling never becomes a fabricated extraction;
- PDF metadata is retained;
- dates are parsed only when explicitly present and valid;
- deadlines require deadline/submission language plus an explicit date;
- events require event language plus an explicit date;
- notice classification is deterministic and has an UNKNOWN outcome;
- academic-calendar rows are normalized without guessing missing dates;
- identifiers are source-relative and stable for the same source/content/key;
- parser versions are persisted in every extracted document;
- extraction quality contains score, level, extraction kind, text length, page count and warnings;
- unsupported media types fail closed;
- extracted records retain evidence ID, source ID and canonical URL;
- repeated fixture extraction is byte-for-byte/model-equal and idempotent.

The gate must not require the live VGU website or paid services.

## Gate 2 — Claim verification

A fixture set must demonstrate:

1. first observation becomes a candidate claim;
2. supported claim becomes verified;
3. unchanged re-fetch is idempotent;
4. changed source creates a new evidence/version record;
5. old claim is superseded rather than overwritten;
6. conflicting evidence is preserved and marked conflicting;
7. unsupported extraction cannot become a student-facing fact.

## Gate 3 — Student information model

The system must expose deterministic records for the initial categories:

- notice;
- academic-calendar item;
- deadline;
- examination information;
- event/resource.

Every published record must retain its authoritative source URL and evidence provenance.

## Gate 4 — Telegram MVP

A test user must be able to:

- start/subcribe without university credentials;
- view latest verified information;
- view upcoming relevant items;
- open the original source;
- inspect verification status;
- avoid duplicate notifications.

Telegram transport failures must not corrupt claim state.

## Gate 5 — Production-free deployment

Before deployment:

- GitHub Actions schedules are bounded;
- D1 schema migrations are reproducible;
- R2 retention is bounded;
- Worker webhook handling is idempotent;
- secrets exist only in provider secret stores;
- free-tier quotas have been checked against expected workload;
- failure/retry behavior is tested.

## Gate 6 — Verification assistant

Only after the deterministic pipeline is trustworthy:

```text
community submission
 → quarantine
 → official-source search
 → evidence comparison
 → explicit result
```

Possible outcomes:

- OFFICIALLY VERIFIED;
- OFFICIAL SOURCE CHANGED/SUPERSEDED;
- CONFLICTING;
- NOT OFFICIALLY CONFIRMED.

No AI-generated assertion is accepted without evidence.

## CI baseline

The default deterministic CI suite should run:

```text
ruff format --check .
ruff check .
mypy src
pytest -q
```

Live-source tests are not the foundation of CI. Committed fixtures are.

## Release rule

A feature is not considered complete because its happy path works. It must have:

- failure behavior;
- idempotency behavior;
- provenance;
- regression coverage;
- explicit security/privacy review where relevant.
