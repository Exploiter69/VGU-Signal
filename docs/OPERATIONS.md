# Operations Guide

VGU Signal is an information-monitoring system. Operational correctness matters because stale or duplicated information can be harmful even when the software itself is available.

## Pipeline health

Track at least:

- last successful fetch per source;
- last changed content per source;
- parser failures;
- verification failures/conflicts;
- notification failures;
- scheduled-job failures;
- source freshness.

## Failure policy

### Fetch failure

Retry with bounded exponential backoff. Preserve the last-known-good state and record the failure.

### Parse failure

Retain the raw evidence. Do not publish newly derived claims from a failed parse.

### Verification conflict

Preserve all relevant evidence and mark the result `CONFLICTING` rather than guessing.

### Notification failure

Retry safely using an idempotency key. A retry must not create a duplicate logical notification.

## Source outage

A VGU source being temporarily unavailable does not mean its previous information is invalid.

The system should distinguish:

- source freshness;
- claim validity/effective period;
- operational availability.

## Monitoring frequency

Use source-specific schedules. More frequent polling is appropriate for notices and deadline-bearing pages; stable policy documents need less frequent checks.

Avoid aggressive polling that creates unnecessary load.

## Deployment

Production deployment must use only documented, reproducible configuration.

Secrets belong in secret storage/environment configuration, never in the repository.

## Zero-cost operations

The production design targets free infrastructure only. Before deployment and whenever provider limits change:

1. verify current free-tier limits;
2. estimate expected usage;
3. configure safeguards;
4. ensure over-limit behavior fails safely;
5. confirm no accidental paid fallback is enabled.

## Recovery

A recovery procedure must eventually document:

- how to redeploy;
- how to restore database state;
- how evidence artifacts are recovered;
- how scheduled jobs are re-enabled;
- how notification state avoids duplicate sends after recovery.

## Operational trust rule

Never hide a data-quality failure merely to make the dashboard or job appear green. A visible failed parse is safer than a successful-looking run that published incorrect information.
