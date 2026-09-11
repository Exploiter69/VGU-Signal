# VGU Signal Trust Model

Trust is the central product requirement. VGU Signal must be more useful than searching manually without becoming less trustworthy than the original VGU source.

## Authority rule

> The official VGU source remains the authority. VGU Signal is a discovery, structuring, verification and delivery layer.

The system must always make it possible to navigate from a claim back to its supporting official source.

## Source hierarchy

Preferred authority order:

1. Official VGU document or notice.
2. Official VGU HTML page.
3. Official VGU-controlled portal/public endpoint.
4. Official VGU social account, primarily as a pointer to authoritative material.
5. Community submission, used only as a discovery/verification signal.

A lower-ranked source cannot silently override a higher-ranked source.

## State machine

```text
DISCOVERED
    ↓
FETCHED
    ↓
PARSED
    ↓
VERIFIED
  ↙   ↓   ↘
CHANGED SUPERSEDED EXPIRED
  ↘   ↓   ↙
CONFLICTING / REMOVED
```

`COMMUNITY_SIGNAL` is a source class, not an authority state.

`UNVERIFIED` means the system has not established sufficient official evidence. It does not automatically mean false.

## Evidence

Every published fact should have a provenance chain:

```text
Claim
  ↓ supported by
Evidence
  ↓ fetched from
Official source URL
```

Evidence should record at least:

- source URL;
- fetch timestamp;
- HTTP status;
- content type;
- raw content hash;
- raw artifact reference when retained;
- extracted-text hash where applicable;
- parser version;
- HTTP validators such as ETag/Last-Modified when available.

## Immutable history

Do not edit history to make the database look clean.

If an official document changes:

```text
old evidence → old claim
new evidence → new claim
                     ↓
                supersedes old
```

This permits the system to explain what changed and when.

## Verification requirements

A claim can be treated as officially verified only when there is sufficient evidence from an authoritative source.

Examples:

- A deadline appears in an official VGU PDF → eligible for verification.
- A student forwards a screenshot of a deadline → community signal only until matched.
- A notice disappears from a page → do not immediately claim it was cancelled; mark the source/document state appropriately and retain last-known evidence.
- Two official sources disagree → `CONFLICTING` until the relationship is resolved by stronger evidence or an explicit newer source.

## Deduplication

Deduplication must preserve provenance.

Signals include:

- canonical URL;
- raw SHA-256;
- normalized title;
- document identifiers;
- publication dates;
- semantic content similarity.

Two identical copies may be one logical document with multiple evidence locations. Do not destroy the evidence of either source.

## Semantic changes

Not every byte change matters equally.

The system should distinguish:

- formatting-only changes;
- metadata changes;
- textual changes;
- deadline/date changes;
- document replacement;
- supersession;
- removal.

Deadline/date changes deserve high priority because they can directly affect students.

## Notifications

Notifications must be based on state transitions, not merely scraper runs.

Example:

```text
FETCHED unchanged → no notification
FETCHED new       → candidate notification
VERIFIED new      → publish
VERIFIED changed  → change notification
SUPERSEDED        → correction/update notification
CONFLICTING       → cautious warning or review
```

A notification should be idempotent.

## Community verification

The future verification assistant may accept voluntary forwarded messages, screenshots or PDFs.

It must respond conservatively:

- **OFFICIALLY VERIFIED** — matching authoritative evidence found.
- **OFFICIAL SOURCE CHANGED/SUPERSEDED** — related source exists but differs.
- **CONFLICTING** — authoritative sources disagree.
- **NOT OFFICIALLY CONFIRMED** — no sufficient official evidence found.

Never claim “fake” solely because a search did not find a matching source.

## AI grounding

AI-generated summaries and explanations must retain the evidence references used to produce them.

The model cannot promote its own output to an authoritative fact.

## Human override

Where evidence is genuinely ambiguous, the safe behavior is to expose uncertainty and request review rather than guess.

The system should be designed so that a human can inspect the evidence chain and understand why a state was assigned.
