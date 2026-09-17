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