# Data Model

This is the conceptual model. It is intentionally implementation-neutral; the physical schema comes after stack selection.

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

Evidence is the audit layer.

## Document

Represents a logical notice, PDF, page or other university publication that may have multiple evidence versions/locations.

```text
Document
- id
- title
- canonical_url
- document_type
- published_at
- current_state
```

## Claim

Represents a normalized fact derived from evidence.

```text
Claim
- id
- document_id
- claim_type
- normalized_value
- status
- effective_from
- effective_until
- first_seen_at
- last_seen_at
- supersedes_claim_id
```

## Deadline / Event

These are domain views over claims rather than independent truth stores.

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

This prevents multiple subsystems from inventing separate versions of the same official fact.

## User

Only minimal data needed for personalization.

```text
User
- id
- telegram_user_id
- created_at
- status
```

## User preferences

```text
UserPreference
- user_id
- program
- branch
- year
- semester
- categories
- quiet_hours
- digest_enabled
```

Exact fields must be finalized after Telegram UX and privacy review.

## Notification

Represents an attempted/delivered user-facing event.

```text
Notification
- id
- user_id
- claim_id / event_id
- notification_type
- created_at
- delivered_at
- delivery_status
```

A stable identity/idempotency key is required so retries cannot produce duplicate alerts.

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

User
  ↓ has
Preferences
  ↓ select
Claims/Events
  ↓ produce
Notifications
```

## Design rule

The database is not the source of truth by itself. For authoritative university facts, the source evidence and provenance chain remain the foundation.
