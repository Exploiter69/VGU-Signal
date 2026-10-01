# Phase 4 — Student Information Model

Phase 4 converts verified Phase 3 claims into a delivery-neutral student information layer. It does not reimplement evidence acquisition or verification.

## Contract

Every InformationItem:

- references exactly one verified claim_id;
- carries a stable category;
- may carry program, branch, year and semester applicability;
- separates importance from urgency;
- retains published/effective/expiry timestamps where known;
- retains one primary official source URL and any additional source links;
- can reference changed, superseded or corrected prior information;
- is searchable without Telegram, Worker or other delivery code.

## Categories

The stable public model is:

- DEADLINE
- EXAM
- FEES
- REGISTRATION
- NOTICE
- EVENT
- HOLIDAY
- CALENDAR

Existing Phase 2 notice categories map deterministically into this model. The mapping is intentionally explicit rather than stringly typed.

## Student dimensions

StudentScope contains optional:

- program
- branch
- year
- semester

A missing dimension means the information is broader than that dimension. Scope matching is conservative and deterministic: incompatible known dimensions do not match; unknown dimensions do not falsely exclude an item.

Applicability remains distinct from truth. A matching student scope does not prove that an official notice applies unless the source content supports that interpretation.

## Importance and urgency

Importance is a relevance signal, not a trust signal.

- Importance: LOW, NORMAL, HIGH, CRITICAL
- Urgency: NONE, UPCOMING, SOON, IMMEDIATE, OVERDUE

The deterministic priority function considers deadline/event proximity, consequence-heavy categories, explicit urgency language, changed/superseding state and scope specificity. It never changes verification state.

## Time model

The item preserves:

- published_at
- effective_from
- effective_until
- due_at
- starts_at
- ends_at

Effective-window checks are half-open: effective_from <= time < effective_until.

## Provenance

source_links and primary_source_url are presentation-safe references to the authoritative source. The authoritative evidence chain remains the Phase 3 claim/provenance model.

## Change history

The information layer can express:

- CHANGED
- SUPERSEDES
- CORRECTS

These relationships preserve old items rather than overwriting them.

## Search archive

InformationArchive and search_archive() provide delivery-neutral deterministic search with:

- free-text matching across title/summary;
- category filtering;
- student-scope filtering;
- effective-time filtering;
- optional expired-item inclusion;
- deterministic ordering.

The same model can therefore be rendered by Telegram, a Worker/API or a future web client without duplicating business logic.

## Durable schema

Migration 0004_information_model.sql adds:

- information_items;
- student applicability dimensions;
- importance/urgency and temporal fields;
- indexed category/scope/time fields;
- information_source_links;
- information_relationships.

The schema references Phase 3 claims and preserves the trust boundary.

## Exit invariant

> A delivery client consumes the same verified InformationItem representation; it does not invent categories, applicability, priority, source links or change history.
