# Phase 0 Implementation Plan

This is the execution plan for moving VGU Signal from architecture documentation into code.

## Objective

Finish Phase 0 without prematurely building the entire product. The output is a small, testable repository skeleton that can safely absorb the first official VGU source.

## Step 1 — Bootstrap the repository

Create:

- Python package under `src/vgu_signal/`;
- `pyproject.toml`;
- dependency lock strategy;
- test configuration;
- Ruff and mypy configuration;
- Worker package under `worker/`;
- D1 migration directory;
- GitHub Actions CI workflow.

## Step 2 — Establish domain contracts

Implement pure, dependency-light types for:

- `Source`;
- `Evidence`;
- `Document`;
- `Claim`;
- `Deadline`;
- `Event`;
- trust states;
- source classes;
- verification outcomes.

These contracts should not know about Telegram, Cloudflare or a particular scraper.

## Step 3 — Establish ports/interfaces

Define interfaces for:

- source acquisition;
- evidence persistence;
- document persistence;
- claim persistence;
- notification delivery;
- clock/time;
- hashing.

Implement local deterministic versions first.

## Step 4 — Build the first fixture

Capture one representative public VGU HTML source as a committed fixture.

The fixture should contain enough structure to test:

- URL identity;
- HTTP metadata representation;
- raw hashing;
- parser version;
- extracted title/date/body/link fields;
- deterministic normalization.

Do not make the test suite depend on the live website being available.

## Step 5 — First source adapter

Implement exactly one official VGU source adapter.

The adapter must:

- have an explicit source ID;
- declare its URL and source class;
- obey bounded HTTP behavior;
- produce evidence;
- parse into normalized documents;
- expose parser failures without publishing unsupported claims.

Choose the simplest high-value source first rather than the hardest page.

## Step 6 — Verification skeleton

Implement the minimum state transitions needed for the first source:

```text
DISCOVERED
  ↓
FETCHED
  ↓
PARSED
  ↓
VERIFIED
  ↓
CHANGED / SUPERSEDED
```

Also implement `CONFLICTING` and `UNVERIFIED` paths in tests even if the first source does not naturally exercise them.

## Step 7 — CI gate

The first CI workflow must reject:

- formatting drift;
- lint errors;
- type errors;
- failing tests.

It must run without secrets and without paid services.

## Step 8 — Update status

Only after the above passes should `docs/STATUS.md` move from “pre-implementation architecture baseline” to “Phase 0 complete / Phase 1 in progress”.

## What we are deliberately not doing yet

- Telegram UX polish;
- broad source crawling;
- browser automation as a default;
- OCR pipeline optimization;
- AI integration;
- student personalization algorithms;
- production deployment;
- private ERP access;
- WhatsApp group ingestion.

## First vertical slice target

The first meaningful implementation should be:

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

Only after this slice is proven should the project widen to more VGU sources.
