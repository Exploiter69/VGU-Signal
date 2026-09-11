# Architecture Decisions

This file records decisions that should not be casually reversed during implementation.

## D001 — Official source remains authoritative

**Decision:** VGU Signal never becomes the authority for university facts.

**Reason:** The product's value is discoverability and delivery, while institutional authority remains with VGU.

## D002 — Evidence before publication

**Decision:** Student-facing claims must have traceable supporting evidence.

**Reason:** A wrong deadline can cause real harm and destroy trust.

## D003 — Immutable claim history

**Decision:** Corrections and supersession create relationships between versions instead of overwriting history.

**Reason:** Students need to know what changed and operators need an audit trail.

## D004 — Source adapters are modular

**Decision:** Scraping/extraction mechanisms are adapters, not the product architecture.

**Reason:** VGU's public site can change, and different sources require different acquisition methods.

## D005 — Deterministic core, optional AI

**Decision:** The core pipeline must work without an AI API.

**Reason:** Reliability, cost control and reproducibility are more important than AI novelty.

## D006 — No authenticated ERP scraping

**Decision:** Do not collect credentials or scrape private ERP/student dashboards.

**Reason:** Privacy, security and authorization boundaries. Legitimate official integrations can be evaluated later.

## D007 — No private WhatsApp scraping

**Decision:** Private groups are not an acquisition source.

**Reason:** Privacy and access boundaries. Voluntary forwarded submissions may later be used as discovery signals.

## D008 — D1/R2 + GitHub Actions target

**Decision:** Heavy scheduled acquisition/parsing is targeted for GitHub Actions; live state is targeted for Cloudflare D1; raw evidence may be retained in R2; a Worker handles lightweight webhook/API traffic.

**Reason:** This separates workloads according to their resource needs while targeting a zero-cost deployment.

Free-tier limits must be verified at deployment time.

## D009 — SQLite is development-only

**Decision:** SQLite may be used for local tests/fixtures, but is not the planned production transactional database.

**Reason:** Concurrent crawler, notification and user interactions are better served by a managed transactional store.

## D010 — Telegram first

**Decision:** Telegram is the first user-facing channel.

**Reason:** It supports bot interactions and notifications without requiring a dedicated mobile application.

## D011 — Conservative verification language

**Decision:** Failure to find an official match means “not officially confirmed,” not automatically “fake.”

**Reason:** Search incompleteness is not proof of falsity.
