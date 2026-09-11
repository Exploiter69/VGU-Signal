# VGU Signal Source Strategy

## Purpose

The source layer defines where VGU Signal is allowed to obtain university information and how each source is handled.

Official VGU sources should be discovered and monitored systematically, but the project must avoid pretending that one crawl covers the entire university.

## Initial official source classes

Priority Tier A:

1. VGU official resources / handbooks page.
2. Academic calendars.
3. Examination rules and examination-cell public notices.
4. Public university notices.
5. Public fee information.
6. Public event information.

Priority Tier B:

- student handbook;
- academic regulations;
- scholarships;
- hostel information;
- other important resources.

Priority Tier C, after the core pipeline is reliable:

- CDOE public pages;
- Online VGU public material;
- department-level public pages;
- official public social accounts;
- additional public university systems.

## Acquisition ladder

Use the cheapest reliable acquisition method:

```text
public sitemap/API/feed
        ↓
ordinary HTTP
        ↓
HTML parsing
        ↓
adaptive extraction if justified
        ↓
browser rendering if genuinely required
        ↓
source-specific adapter
```

The project must not make a particular scraping framework a single point of failure.

## Robots and site policy

Before adding a source adapter:

1. inspect robots.txt when available;
2. inspect sitemap information;
3. identify public vs authenticated paths;
4. use reasonable request rates;
5. avoid unnecessary crawling;
6. record source assumptions in the registry.

A robots restriction or site-policy concern is an engineering input, not something to work around by stealth.

## Public vs authenticated systems

Public VGU pages and documents are in scope.

Authenticated student systems are **not** part of the normal acquisition pipeline.

Never request or store:

- ERP passwords;
- session cookies;
- access tokens supplied by students;
- scraped private dashboards.

An official API or authorized read-only integration may be evaluated later as a separate architecture track.

## Source registry

Each source should eventually have metadata similar to:

```text
Source
- id
- name
- authority
- base_url
- source_type
- acquisition_method
- crawl_frequency
- parser
- enabled
- policy_notes
- last_success_at
- last_failure_at
```

This makes source behavior explicit rather than scattering URLs through code.

## Discovery vs publication

Discovery is not publication.

A source can produce a candidate document without that document immediately becoming a trusted student-facing claim. Evidence, extraction and verification still apply.

## Change detection

Prefer conditional requests using ETag/Last-Modified where supported. Always retain a content hash as a robust fallback.

For HTML, consider a meaningful-content representation so navigation chrome or timestamps do not cause noisy alerts.

For PDFs and other documents, compare raw hashes and then classify meaningful changes.

## Frequency

Frequency should be source-specific.

Examples:

- notices / circulars: more frequent;
- academic calendars: daily is usually sufficient;
- stable policies: less frequent;
- event pages: more frequent around active event periods.

Do not create excessive load merely to reduce an already-small latency.

## Source failures

A temporary source failure must not erase previously verified information.

```text
source unavailable
      ↓
retry/backoff
      ↓
last-known-good remains current
      ↓
record operational failure
```

If a source remains unavailable, its freshness state should be visible internally.

## Source-specific adapters

Adapters may normalize peculiar VGU structures, but they must output a common internal representation.

An adapter should not contain:

- Telegram formatting;
- user preference logic;
- AI prompts;
- notification policy;
- unrelated database mutation logic.

## Community sources

Community submissions are useful for discovering information that the official crawler may have missed.

They are not authoritative.

```text
community signal
      ↓
search official sources
      ↓
match evidence
      ↓
verify / conflict / unverified
```

Private group scraping is out of scope.
