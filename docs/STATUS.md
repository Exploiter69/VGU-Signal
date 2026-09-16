# Project Status

**As of 2026-09-16**

## Current stage

**Phase 1 — Source Discovery & Evidence Engine: COMPLETE.**

Phase 0 remains closed and unchanged. Phase 1 has now implemented the first deterministic source/evidence layer: an explicit official-source inventory, bounded HTTP acquisition, robots/sitemap policy handling, content/status validation, raw SHA-256 identity, conditional requests, retry/backoff, rate limiting, immutable local evidence semantics, last-known-good behavior, acquisition failure reporting and fixture-backed regression tests.

## Phase 1 source inventory

The admitted official public sources are documented in `docs/SOURCE_INVENTORY.md`:

- VGU official resources / handbooks / academic-calendar index;
- VGU 2026-27 first-year academic calendar PDF;
- VGU Examination Rules 2.0 PDF;
- VGU public CDOE notice PDF;
- VGU public fee information page;
- VGU public events page.

Academic-calendar discovery remains anchored on the official resources index, while the verified 2026-27 first-year calendar is also registered as a direct evidence target. Authenticated ERP material and private student/community sources remain excluded.

## Phase 1 implementation checklist

- [x] Source registry with stable IDs and allowed media types.
- [x] HTTP acquisition adapter.
- [x] Bounded streaming response size.
- [x] HTTP status validation.
- [x] Content-type validation.
- [x] Raw response SHA-256 hashing.
- [x] ETag conditional requests.
- [x] Last-Modified conditional requests.
- [x] Retry/backoff for transient failures.
- [x] `Retry-After` handling.
- [x] Minimum request interval/rate limiting.
- [x] Robots policy evaluation.
- [x] Sitemap declaration parsing.
- [x] Sitemap XML URL parsing.
- [x] Immutable local evidence store semantics.
- [x] Same-content deduplication.
- [x] Changed-content history preservation.
- [x] Last-known-good behavior after acquisition failure.
- [x] Durable D1 acquisition-run metadata migration.
- [x] Failure observability fields.
- [x] Fixture-backed HTTP tests.
- [x] Fixture-backed policy tests.
- [x] Fixture-backed acquisition/change/failure tests.
- [x] Source registry tests.
- [x] Full CI quality gate after implementation and documentation synchronization.

## Phase 1 exit gate

The phase is considered closed only because the deterministic tests prove all required transitions without relying on the live VGU website:

```text
first fetch       → FETCHED
same raw hash     → UNCHANGED
new raw hash      → CHANGED
conditional 304   → UNCHANGED
fetch failure     → FAILED + last-known-good preserved
```

Earlier evidence is never overwritten when a new content state arrives. A failed acquisition cannot erase the last-known-good evidence state.

## Trust and safety invariants retained

- Official public VGU sources remain authoritative.
- Evidence identity is based on exact raw bytes, not an AI interpretation.
- Discovery does not equal publication or verification.
- Robots restrictions are honored rather than bypassed.
- Authenticated ERP and private WhatsApp data remain out of scope.
- The Phase 1 core has no paid-service dependency.
- Live website availability is not required for CI.

## Phase 2 readiness

**Phase 2 is now unblocked.** Its prerequisites are the stable source IDs, evidence IDs, raw-content history and deterministic acquisition outcomes produced by Phase 1.

Phase 2 may now add PDF/HTML extraction, date/deadline extraction, event extraction, notice classification, academic-calendar normalization, source-relative identifiers and extraction quality signals. It must consume Phase 1 evidence rather than bypassing the acquisition layer.
