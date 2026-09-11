# VGU Signal Architecture

## 1. System objective

VGU Signal is a durable information pipeline, not a scraper with a chatbot attached.

Its job is to discover public VGU information, preserve evidence, extract structured facts, determine their state, personalize them and deliver them through one or more interfaces.

The architecture is deliberately source-agnostic and delivery-agnostic.

## 2. High-level architecture

```text
                 OFFICIAL VGU PUBLIC SOURCES
        ┌──────────────┬──────────────┬──────────────┐
        │ HTML pages   │ PDFs         │ Event pages  │
        │ Resources    │ Calendars    │ Notices      │
        └──────┬───────┴──────┬───────┴──────┬───────┘
               │              │              │
               └──────────────┼──────────────┘
                              ↓
                     SOURCE REGISTRY
                              ↓
                       ACQUISITION
                              ↓
                       EVIDENCE STORE
                              ↓
                  EXTRACTION / NORMALIZATION
                              ↓
                   VERIFICATION / DEDUPE
                    /        │        \
                   /         │         \
             CURRENT       HISTORY    CONFLICTS
                   \         │         /
                    \        │        /
                     INFORMATION MODEL
                              ↓
                    PERSONALIZATION ENGINE
                       /                 \
                      ↓                   ↓
                 TELEGRAM               WEB/API
```

## 3. Architectural boundaries

### Source layer
Knows how to discover and fetch public VGU material. It must not contain student-specific business logic.

### Evidence layer
Stores immutable or content-addressed evidence metadata and references to raw artifacts. Evidence is the foundation for auditability.

### Extraction layer
Converts bytes into deterministic structured representations. It must not decide whether a claim is true merely because extraction succeeded.

### Verification layer
Determines relationships between evidence and claims: verified, changed, superseded, conflicting, expired, removed, etc.

### Information model
Contains normalized university information that clients can query.

### Personalization layer
Maps verified information to user preferences and notification policies.

### Delivery layer
Telegram, web and future clients render information. Delivery must not mutate authoritative facts.

## 4. Production deployment target

```text
VGU public web
      │
      ▼
GitHub Actions
  ├─ discovery
  ├─ HTTP fetch
  ├─ PDF parsing
  ├─ OCR when required
  ├─ hashing
  └─ normalization
      │
      ├──────────────► Cloudflare R2
      │                 raw evidence
      ▼
Cloudflare D1
  ├─ sources
  ├─ evidence metadata
  ├─ claims
  ├─ events/deadlines
  ├─ users/preferences
  └─ notification state
      │
      ▼
Cloudflare Worker
  ├─ Telegram webhook
  └─ lightweight API
      │
      ▼
Telegram
```

GitHub Actions handles heavy work because edge request execution is intentionally lightweight. The Worker should not become a PDF/OCR processing engine.

## 5. Acquisition ladder

Use the least complex reliable method for each source:

```text
1. robots.txt / sitemap / public API / feed
        ↓
2. ordinary HTTP
        ↓
3. HTML parser / deterministic extraction
        ↓
4. adaptive extraction when justified
        ↓
5. browser rendering for genuinely client-rendered content
        ↓
6. source-specific special handling
```

A browser or adaptive scraper is an adapter, never the architecture.

## 6. Evidence model

Conceptual evidence record:

```text
Evidence
- id
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

The raw hash is a content identity signal. Parser versioning allows extraction behavior to evolve without pretending that old interpretations were produced by the new parser.

## 7. Claim model

A claim represents a normalized statement derived from one or more evidence records.

Conceptually:

```text
Claim
- id
- claim_type
- normalized_value
- status
- first_seen_at
- last_seen_at
- effective_from
- effective_until
- supersedes_claim_id
```

A claim must be traceable to its supporting evidence. A correction creates a new claim and preserves the old relationship/history.

## 8. Change detection

At minimum, detect:

- URL disappeared.
- HTTP content changed.
- Raw content hash changed.
- Extracted meaningful content changed.
- Document metadata changed.
- Deadline/date changed.
- A newer notice supersedes an older one.

Do not treat every byte-level change as a student-visible change. Separate raw change detection from semantic change classification.

## 9. Idempotency

The same input processed twice should not create duplicate information or duplicate notifications.

Examples:

- Same URL + same raw SHA-256 → no new evidence version.
- Same semantic claim already current → no duplicate claim.
- Same notification event already delivered → do not send again.
- Failed processing can be retried safely.

## 10. Failure handling

The pipeline should prefer explicit failure over silent corruption.

```text
fetch failure
   → retry with backoff
   → if persistent, retain last-known-good state
   → record failure
   → alert/observe
```

```text
parse failure
   → retain raw evidence
   → mark parse failure
   → do not publish derived facts
```

```text
verification conflict
   → preserve both evidence paths
   → mark CONFLICTING
   → do not silently select a winner
```

## 11. AI boundary

AI is an optional augmentation layer.

Allowed:

- summarize verified documents;
- explain difficult wording;
- assist semantic retrieval;
- classify ambiguous material for review;
- match a community submission against official evidence.

Not allowed:

- invent deadlines;
- override source evidence;
- turn a rumor into an official claim;
- silently modify authoritative dates;
- decide that an official source is wrong without evidence.

## 12. Security boundary

Authenticated VGU systems are outside the public acquisition pipeline unless an explicit, legitimate integration is later established.

The system must never require:

- student ERP passwords;
- session cookies;
- scraped private dashboards;
- private WhatsApp group access.

## 13. Development architecture

SQLite may be used for local development and deterministic fixtures. It is not the planned production transactional database.

The codebase should keep these concerns separately testable:

```text
sources/
acquisition/
evidence/
extractors/
verification/
models/
notifications/
telegram/
storage/
```

Exact package layout may change during implementation; the boundaries should not.
