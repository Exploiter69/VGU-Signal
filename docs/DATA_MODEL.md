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

## Information item

The stable student-facing information representation is a delivery-neutral projection of a verified claim.

InformationItem
- id
- claim_id
- title
- summary
- category
- program
- branch
- year
- semester
- importance
- urgency
- published_at
- effective_from
- effective_until
- due_at
- starts_at
- ends_at
- primary_source_url
- supersedes_item_id
- changed_from_item_id
- corrected_item_id

Categories are explicit: DEADLINE, EXAM, FEES, REGISTRATION, NOTICE, EVENT, HOLIDAY and CALENDAR.

Program/branch/year/semester are optional applicability dimensions. Missing dimensions are broader scope, while incompatible known dimensions do not match. Applicability does not establish truth.

Importance and urgency are separate relevance signals:

- Importance: LOW / NORMAL / HIGH / CRITICAL.
- Urgency: NONE / UPCOMING / SOON / IMMEDIATE / OVERDUE.

These signals never replace verification.

Effective windows use published/effective/expiry timestamps. Deadline and event timing is preserved separately so clients do not need to infer dates from prose.

## Information source links

information_source_links preserves the primary official URL and any additional source URLs for an information item. The Phase 3 evidence/provenance chain remains the authoritative audit trail.

## Information relationships

information_relationships preserves non-destructive student-facing history:

- CHANGED;
- SUPERSEDES;
- CORRECTS.

Old information remains queryable.

## Searchable archive

The information archive supports deterministic search by text, category, student scope and effective time. Expired records are excluded by default when a reference time is supplied, with an explicit option to include them.

## Phase 4 boundary

Information items may only be constructed for publication through the Phase 3 verified-claim guard. Delivery clients consume InformationItem records and do not recreate category, scope, priority, provenance or history rules.

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

## Telegram user and preferences

Migration 0005_telegram_mvp.sql adds:

~~~
User
- id
- telegram_user_id
- created_at
- updated_at
- status

UserPreference
- user_id
- program
- branch
- year
- semester
- categories_json
- digest_enabled
- reminders_enabled
- muted
- quiet_start
- quiet_end

TelegramSession
- user_id
- flow
- step
- updated_at
~~~

Preferences are user-declared relevance filters. They do not prove that an official notice applies.

## Notification

~~~
Notification
- id
- user_id
- information_item_id
- notification_type
- scheduled_key
- created_at
- delivered_at
- delivery_status
~~~

The unique user/item/type/scheduled-key identity provides durable notification deduplication.

## Phase 5 query boundary

Telegram reads current VERIFIED claims joined to InformationItem records. Items already replaced through a CHANGED, SUPERSEDES or CORRECTS relationship are excluded from current delivery queries. Historical rows remain durable.


## Phase 6 operational data

```
PipelineRun
- id
- started_at
- finished_at
- status
- source_count
- fetched_count
- changed_count
- failed_count
- error_summary

SourceHealth
- source_id
- last_attempt_at
- last_success_at
- last_status
- consecutive_failures
- last_error

BackupManifest
- id
- created_at
- manifest_hash
- object_count
- byte_count
- r2_prefix
```

Operational state supplements, but does not replace, the evidence/provenance model.
