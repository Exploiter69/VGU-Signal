# Project Status

**As of 2026-09-16**

## Current stage

**Phase 0 — Repository foundation and contracts: COMPLETE.**

The repository bootstrap, deterministic implementation skeleton, fixture/test foundation and CI quality gates are complete. The final Phase 0 verification revision passed the full CI gate, and the roadmap/status documentation has now been synchronized to that result.

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
- [x] Strict Python typing for the bootstrap source tree.
- [x] Final Ruff format check.
- [x] Final Ruff lint check.
- [x] Final mypy check.
- [x] Final pytest suite.
- [x] Final Worker typecheck.

The verified Phase 0 CI run executed this complete gate on the same verification revision:

```text
ruff format --check .   PASS
ruff check .            PASS
mypy src                 PASS
pytest -q                PASS
worker npm run typecheck PASS
```

## Phase 0 implementation baseline

The repository has the minimum deterministic implementation surface needed to begin the first real source/evidence vertical slice without reopening the core architecture. The source registry contains an initial official VGU resources entry; HTTP acquisition is bounded and hashes raw content; the domain layer defines source/evidence/document/claim contracts; HTML extraction is fixture-testable; and the initial D1 migration establishes source/evidence persistence primitives.

The strict typing/test corrections made during verification are part of the baseline rather than deferred cleanup: URL fields are represented consistently with the domain contract, HTML link normalization is validated by fixture tests, and the source tree passes strict mypy.

## Phase 1 readiness

**Phase 1 is now unblocked.** The next implementation stage is **Source Discovery & Evidence Engine**:

1. confirm and document the initial official source set;
2. implement the source registry as the authoritative acquisition inventory;
3. implement HTTP acquisition with robots/sitemap policy, conditional requests, retry/backoff and rate limits;
4. persist immutable evidence and raw-content hashes;
5. implement last-known-good behavior;
6. add change detection and failure observability;
7. validate the first real official VGU source end-to-end with committed fixtures.

Phase 1 must preserve all Phase 0 invariants: official sources remain authoritative, evidence remains immutable/traceable, unsupported extraction cannot become a student-facing fact, and core operation remains compatible with the ₹0 / $0 requirement.

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
