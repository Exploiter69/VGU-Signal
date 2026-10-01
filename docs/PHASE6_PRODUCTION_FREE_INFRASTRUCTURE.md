# Phase 6 — Production-Free Infrastructure

**Status: COMPLETE after the Phase 6 verification revision.**

## Objective

Operate VGU Signal at $0 using GitHub Actions for acquisition/processing, Cloudflare D1 for live state and immutable raw evidence, and the existing Worker for Telegram/API delivery.

## Target architecture

~~~text
VGU public sources
      ↓
GitHub Actions — bounded fetch / parse / verify
      ↓
Cloudflare D1 — live state + content-addressed evidence chunks
      ↓
Cloudflare Worker — webhook/API + scheduled notifications
      ↓
Telegram
~~~

## Implementation

- Six-hour scheduled GitHub Actions acquisition with manual dispatch.
- Deterministic extraction, verification and InformationItem generation.
- Private, content-addressed D1 evidence chunks: `evidence_blobs(evidence_id, chunk_index, data)`, with 32 KiB chunks below D1's 2 MiB row limit.
- D1 migration `0006_operations.sql` for pipeline runs, source health and backup manifests.
- Worker D1 binding and existing 15-minute notification Cron; no object-storage binding is required.
- Worker health checks D1 without exposing stored evidence.
- Acquisition: 20-second timeout, 10 MiB response cap, two retries, exponential backoff/Retry-After and one-second inter-request spacing.
- Complete source outage fails the workflow; partial failures retain successful state and are visible in the run manifest.
- Recovery uses migration replay plus deterministic pipeline replay; raw evidence is content-addressed in D1.
- Secrets are never committed.

## Secrets

GitHub Actions:
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `D1_DATABASE_ID`

Worker:
- `TELEGRAM_BOT_TOKEN`
- optional `TELEGRAM_WEBHOOK_SECRET`

## Free-tier guardrails

As of October 2026, Cloudflare documents Workers Free at 100,000 requests/day and 10 ms CPU per invocation. D1 is available on Workers Free with 5 million rows read/day, 100,000 rows written/day and 5 GB total account storage; an individual Free database is limited to 500 MB and a BLOB/row to 2 MB. D1 free daily limits are enforced, so exhaustion is treated as service degradation rather than a paid fallback. citeturn0search0turn1search6

No paid API, queue, database, hosting or LLM is required.

## Deployment checklist

1. Create D1 database `vgu-signal`.
2. No R2 bucket or billing activation is required.
3. Add the GitHub Actions Cloudflare secrets.
4. Run the acquisition workflow manually.
5. Deploy the Worker.
6. Set Telegram Worker secrets.
7. Configure the Telegram webhook and matching secret.
8. Exercise health and Telegram commands.
9. Confirm D1 evidence chunks and information rows.
10. Confirm reminder/digest behavior against seeded verified data.
11. Retain the first successful run manifest.

Account-specific resource creation remains user-controlled.

## Exit gate

**COMPLETE.**

The repository contains scheduled bounded acquisition, durable operational state, immutable D1 evidence policy, Worker resource bindings and health checks, secret management, failure/retry behavior, recovery procedure and free-tier guardrails without a paid dependency.
