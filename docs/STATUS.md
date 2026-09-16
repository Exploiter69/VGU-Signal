# Project Status

**As of 2026-09-16**

## Current stage

VGU Signal has completed the **Phase 0 repository foundation and implementation-planning baseline**. The repository bootstrap is implemented; the remaining Phase 0 exit condition is the final deterministic CI verification of the bootstrap against the current source tree.

The repository contains the foundational product, architecture, trust, source, security and privacy contracts plus the concrete technical stack, quality gates, implementation plan, domain contracts, acquisition/extraction skeleton, source registry, migration foundation, fixtures/tests and CI workflow.

## Phase 0 verification checklist

- [x] Repository foundation.
- [x] Product thesis.
- [x] Architecture.
- [x] Trust model.
- [x] Source strategy.
- [x] Product scope and non-goals.
- [x] Privacy/security boundaries.
- [x] Concrete implementation stack.
- [x] Python project configuration.
- [x] Worker configuration and typecheck command.
- [x] D1 migration foundation.
- [x] Domain contracts.
- [x] Acquisition skeleton.
- [x] Extraction skeleton.
- [x] Source registry.
- [x] Fixture/test foundation.
- [x] Quality-gate specification.
- [x] CI pipeline.
- [x] Strict Python typing fixes for the bootstrap source tree.
- [ ] Final CI pass on the current Phase 0 source tree.

The CI gate is intentionally conjunctive:

```text
ruff format --check .
        ↓
ruff check .
        ↓
mypy src
        ↓
pytest -q
        ↓
worker npm run typecheck
```

Phase 0 is not considered exited until every required check passes on the same revision.

## Phase 0 implementation baseline

The repository now has the minimum deterministic implementation surface needed to begin the first real source/evidence vertical slice without reopening the core architecture. The source registry contains an initial official VGU resources entry; HTTP acquisition is bounded and hashes raw content; the domain layer defines source/evidence/document/claim contracts; HTML extraction is fixture-testable; and the initial D1 migration establishes source/evidence persistence primitives.

## Phase 1 readiness

Phase 1 remains blocked until the Phase 0 CI gate is green. Once green, implementation proceeds to **Source Discovery & Evidence Engine**:

1. confirm and document the initial official source set;
2. implement the source registry as the authoritative acquisition inventory;
3. implement HTTP acquisition with robots/sitemap policy, conditional requests, retry/backoff and rate limits;
4. persist immutable evidence and raw-content hashes;
5. implement last-known-good behavior;
6. add change detection and failure observability;
7. validate the first real official VGU source end-to-end with committed fixtures.

## Definition of success for the first usable release

A student can:

1. subscribe without giving university credentials;
2. receive a relevant official VGU update;
3. see what changed and why it matters;
4. open the original VGU source;
5. distinguish current information from superseded/conflicting information;
6. avoid duplicate alerts.

## Important note

The project should not be considered production-ready merely because the bot can scrape a page or send a Telegram message. The evidence and verification gates are part of the product, not optional polish.
