# Data Model

VGU Signal keeps the authoritative evidence chain separate from delivery concerns. The physical schema now includes the Phase 3 trust layer while later student-facing fields remain intentionally deferred.

## Source

Represents a configured public information source.

```text
Source
- id
- name
- authority
- base_url
- source_type
- acquisition_method
- crawl_policy
- enabled
- policy_notes
```

## Evidence

Represents a fetched source artifact/version.

```text
Evidence
- id
- source_id
- source_url
- fetched_at
- http_status
- content_type
- raw_content_hash
- raw_content_ref
- extracted_text_hash
- parser_version
- http_last_modified
- http_etag
```

Evidence is immutable audit history. The raw-content hash is the identity fallback even when HTTP validators are unavailable.

## Document

Represents an extracted logical publication backed by one evidence version.

```text
Document
- id
- evidence_id
- source_id
- canonical_url
- title
- published_at
- body_text
- parser_version
- state
```

## Claim

Represents a deterministic fact candidate derived from a document and its evidence.

```text
Claim
- id
- document_id
- evidence_id
- source_id
- statement
- normalized_statement
- fingerprint
- state
- first_seen_at
- last_seen_at
- effective_from
- effective_until
- supersedes_claim_id
- correction_of_claim_id
```

A claim begins `UNVERIFIED`. It cannot become publishable merely because extraction succeeded.

## Claim evidence

The `claim_evidence` relation explicitly links claims to the evidence records supporting them. This allows provenance to survive deduplication and later multi-evidence relationships.

## Claim relationships

`claim_relationships` records non-destructive relationships:

- `SAME_CONTENT`;
- `URL_REPLACEMENT`;
- `SIMILAR`;
- `SUPERSEDES`;
- `CORRECTS`;
- `CONFLICTS`.

Relationships never delete either endpoint. A conflict does not select a winner automatically.

## Verification decisions

`verification_decisions` records the state, reason and decision time so verification is auditable instead of being an unexplained boolean.

## Correction history

`correction_history` preserves explicit correction events and both claim identities. Previous information remains queryable.

## Deadline / Event

These remain domain views over verified claims rather than independent truth stores.

```text
Deadline
- claim_id
- due_at
- audience
- category

Event
- claim_id
- starts_at
- ends_at
- location
- audience
```

Later Phase 4 work will finalize student dimensions and delivery-specific fields.

## User / preferences / notification

These remain deferred until the Telegram/student information phases:

```text
User
- id
- telegram_user_id
- created_at
- status

UserPreference
- user_id
- program
- branch
- year
- semester
- categories
- quiet_hours
- digest_enabled

Notification
- id
- user_id
- claim_id / event_id
- notification_type
- created_at
- delivered_at
- delivery_status
```

## Relationships

```text
Source
  ↓ produces
Evidence
  ↓ describes
Document
  ↓ supports
Claim
  ├── Deadline
  └── Event

Claim ── claim_evidence ──> Evidence
Claim ── claim_relationships ──> Claim
Claim ── verification_decisions
Claim ── correction_history ──> Claim

User
  ↓ has
Preferences
  ↓ select
Claims/Events
  ↓ produce
Notifications
```

## Design rule

The database is not the source of truth by itself. For authoritative university facts, the exact source evidence, evidence hash and provenance chain remain the foundation. Verification state controls publication; history is never overwritten.
