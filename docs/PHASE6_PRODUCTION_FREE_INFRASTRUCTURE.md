# Phase 6 — Production-Free Infrastructure

**Status: COMPLETE after the Phase 6 verification revision.**

## Objective

Operate VGU Signal at $0 using GitHub Actions for acquisition/processing, Cloudflare R2 for immutable raw evidence, Cloudflare D1 for live state, and the existing Worker for Telegram/API delivery.

## Target architecture

~~~text
VGU public sources
      ↓
GitHub Actions — bounded fetch / parse / verify
      ↓
Cloudflare R2 — immutable raw evidence
      ↓
Cloudflare D1 — live application state
      ↓
Cloudflare Worker — webhook/API + scheduled notifications
      ↓
Telegram
~~~

## Implementation

- Six-hour scheduled GitHub Actions acquisition with manual dispatch.
- Deterministic extraction, verification and InformationItem generation.
- Private, content-addressed R2 evidence objects: `evidence/<source-id>/<sha256>.bin`.
- D1 migration `0006_operations.sql` for pipeline runs, source health and backup manifests.
- Worker D1/R2 bindings and existing 15-minute notification Cron.
- Worker GET health checks both D1 and R2 without exposing evidence.
- Acquisition: 20-second timeout, 10 MiB response cap, two retries, exponential backoff/Retry-After and one-second inter-request spacing.
- Complete source outage fails the workflow; partial failures retain successful state and are visible in the run manifest.
- Recovery uses migration replay plus deterministic pipeline replay; raw evidence is content-addressed.
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

As of October 2026, Cloudflare documents Workers Free at 100,000 requests/day and 10 ms CPU per invocation; D1 Free at 5 million rows read/day, 100,000 rows written/day and 5 GB storage; and R2 Free at 10 GB-month storage, 1 million Class A operations/month and 10 million Class B operations/month. D1 free daily limits are enforced, so exhaustion is treated as service degradation rather than a paid fallback. citeturn1search0turn1search2

No paid API, queue, database, hosting or LLM is required.

## Deployment checklist

1. Create D1 database `vgu-signal`.
2. Create private R2 bucket `vgu-signal-evidence`.
3. Add the GitHub Actions Cloudflare secrets.
4. Run the acquisition workflow manually.
5. Deploy the Worker.
6. Set Telegram Worker secrets.
7. Configure the Telegram webhook and matching secret.
8. Exercise health and Telegram commands.
9. Confirm R2 evidence and D1 information rows.
10. Confirm reminder/digest behavior against seeded verified data.
11. Retain the first successful run manifest.

Account-specific resource creation remains user-controlled.

## Exit gate

**COMPLETE.**

The repository contains scheduled bounded acquisition, durable operational state, immutable R2 evidence policy, Worker resource bindings and health checks, secret management, failure/retry behavior, recovery procedure and free-tier guardrails without a paid dependency.
