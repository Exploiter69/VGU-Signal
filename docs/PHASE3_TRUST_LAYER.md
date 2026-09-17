# Phase 3 — Verification, Deduplication & Change History

## Purpose

Phase 3 turns deterministic Phase 2 extraction candidates into an explicit trust layer. It does not use AI, does not fetch URLs, and does not choose a winner when evidence conflicts. A claim is publishable only when it is verified and its evidence record is available.

## Evidence → claim model

Every `EvidenceClaim` contains:

- claim ID;
- document ID;
- Phase 1 evidence ID;
- source ID;
- original statement;
- deterministic normalized statement;
- SHA-256 claim fingerprint;
- verification state;
- first/last observation timestamps;
- optional effective interval;
- optional superseded/corrected claim references.

Extraction output starts as `UNVERIFIED`. Creating a claim can never implicitly verify it.

## Verification state machine

Supported states:

```text
UNVERIFIED
   ├── VERIFIED
   ├── CONFLICTING
   └── REMOVED

VERIFIED
   ├── CONFLICTING
   ├── SUPERSEDED
   ├── EXPIRED
   └── REMOVED

CONFLICTING
   ├── VERIFIED
   ├── SUPERSEDED
   ├── EXPIRED
   └── REMOVED

EXPIRED ──→ VERIFIED / REMOVED
SUPERSEDED ──→ terminal
REMOVED ──→ terminal
```

Illegal transitions raise an error. This prevents accidental resurrection of superseded or removed claims.

## Same-content deduplication

Claims are normalized deterministically and fingerprinted with SHA-256. Identical fingerprints are treated as the same content for deduplication. The first observed candidate remains the retained representative in an in-memory deterministic operation; the relationship layer records duplicate evidence when multiple claims exist.

Deduplication never discards the underlying Phase 1 evidence. Evidence history remains immutable.

## URL replacement detection

A URL replacement is detected only when:

1. source IDs are identical;
2. source-relative logical identifiers are identical;
3. canonical URL identities differ.

The detector does not assume that two similarly named URLs represent the same publication. The logical source-relative identifier must already establish that relationship.

## Cross-source similarity

Different sources are compared using deterministic token-set Jaccard similarity. Similarity creates a `SIMILAR` relationship only; it never automatically verifies, merges or publishes a claim.

This is intentionally separate from conflict detection because two official sources may repeat the same announcement without being contradictory.

## Conflict detection

Conflict detection is conservative and reviewable:

- claims must come from the same source;
- normalized content must differ;
- token overlap must meet a deterministic threshold;
- the system records a `CONFLICTS` relationship instead of selecting a winner.

Different-source disagreements remain relationships that require policy/review rather than an automatic winner.

## Supersession and correction

Supersession and correction are explicit relationships:

- `SUPERSEDES`: a newer claim replaces the operational validity of an older claim;
- `CORRECTS`: a newer claim explicitly fixes an earlier claim;
- the older claim remains in history and is not overwritten.

These relationships are separate from similarity and conflict so later delivery code can explain why an older item is no longer current.

## Expiration

Claims may carry `effective_from` and `effective_until`. At or after `effective_until`, a claim resolves to `EXPIRED`. Expiration never upgrades an unverified claim and never removes evidence.

## Publication guard

`publishable(claim, evidence_ids)` is the trust boundary for student-facing publication. It returns true only when:

```text
claim.state == VERIFIED
AND
claim.evidence_id exists in the available evidence set
```

Therefore a deadline, notice or event cannot become publishable without an evidence chain.

## Human-readable provenance

A provenance record exposes:

```text
claim → document → evidence → source URL
```

and includes evidence hash, observed time, effective interval and supersession/correction references. The source URL is informational navigation; the exact evidence ID/hash remains the audit identity.

## Durable schema

Migration `0003_trust_layer.sql` adds:

- `documents`;
- `claims`;
- `claim_evidence`;
- `claim_relationships`;
- `verification_decisions`;
- `correction_history`.

Foreign keys preserve the evidence chain and indexes support fingerprint, source/state and relationship lookup.

## Regression strategy

Fixture tests cover both false-positive and false-negative boundaries:

- unrelated same-source text does not become a conflict;
- different-source overlap becomes similarity, not conflict;
- identical content deduplicates;
- changed content does not deduplicate;
- URL replacement requires the same logical source-relative identity;
- missing evidence cannot verify or publish a claim;
- illegal state transitions fail;
- superseded/removed claims cannot be silently resurrected;
- expiration is deterministic;
- provenance retains claim/evidence/source linkage.

All Phase 3 tests are local and deterministic. No VGU network access, paid service, OCR binary or LLM is required.

## Trust invariant

> A structured candidate is not authority. Publication requires an explicit verification state and an intact evidence chain, while every prior state remains auditable.
