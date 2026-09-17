# Project Status

**As of 2026-09-17**

## Current stage

**Phase 3 — Verification, Deduplication & Change History: COMPLETE.**

Phase 0, Phase 1 and Phase 2 remain closed. Phase 3 now establishes the trust boundary between deterministic extraction candidates and student-facing publication.

## Phase 3 implementation

The trust layer is evidence-first and fail-closed:

- claims retain document ID, Phase 1 evidence ID, source ID and deterministic fingerprint;
- claim creation always starts `UNVERIFIED`;
- verification requires a matching available evidence ID;
- legal verification state transitions are explicitly constrained;
- same-content duplicates are detected by normalized SHA-256 fingerprint;
- URL replacement requires the same source-relative logical identity and a changed canonical URL;
- cross-source overlap is represented as `SIMILAR`, never automatically merged or verified;
- same-source high-overlap differences are surfaced as `CONFLICTS` for review;
- supersession and correction relationships preserve historical claims;
- effective intervals provide deterministic expiration;
- publication requires `VERIFIED` state and an available evidence record;
- human-readable provenance retains claim → document → evidence → source URL;
- migration `0003_trust_layer.sql` provides durable documents, claims, evidence links, relationships, verification decisions and correction history.

## Phase 3 regression coverage

The deterministic suite covers:

- evidence-to-claim provenance and non-implicit verification;
- missing-evidence rejection;
- publication guard rejection/acceptance;
- same-content deduplication;
- cross-source similarity and threshold validation;
- same-source conflict detection;
- URL replacement positive and negative cases;
- supersession, correction and conflict relationships;
- deterministic expiration;
- legal and illegal state transitions;
- human-readable provenance;
- stable claim fingerprinting;
- malformed evidence-hash rejection.

Tests are fixture/generated-input based and do not require the live VGU website, paid services, OCR binaries or LLMs.

## Phase 3 exit gate

**COMPLETE.** The trust-layer tests demonstrate that no deadline/notice/event candidate can pass the publication guard without both an explicit `VERIFIED` state and a traceable evidence record. Changed, conflicting, superseded and expired states remain explicit rather than overwriting history.

The synchronized quality gate for the revision is:

```text
ruff format --check .
ruff check .
mypy src
pytest -q
worker: npm install && npm run typecheck
```

## Trust and safety invariants retained

- Official public VGU sources remain authoritative.
- Evidence identity is based on exact raw bytes, not an AI interpretation.
- Extraction candidates never become verified merely because they were parsed.
- Conflicts do not select an automatic winner.
- Historical evidence and claim states are retained rather than overwritten.
- Discovery does not equal publication or verification.
- Robots restrictions are honored rather than bypassed.
- Authenticated ERP and private WhatsApp data remain out of scope.
- No paid-service dependency is introduced by Phase 3.

## Next gate

**Phase 4 — Student Information Model.** Phase 4 can now consume verified claims without reimplementing evidence, verification, deduplication or history logic.
