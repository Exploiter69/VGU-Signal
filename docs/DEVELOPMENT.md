# Development Guide

## Engineering philosophy

VGU Signal should be built as a small, testable information system rather than a collection of scripts.

Prefer:

- deterministic behavior;
- explicit contracts;
- immutable evidence/history;
- idempotent jobs;
- small adapters;
- fixture-driven tests;
- observable failures;
- boring infrastructure where possible.

Avoid:

- hidden global state;
- scraper-specific business logic;
- silent fallback to guessed data;
- LLM-first architecture;
- credentials embedded in development tooling.

## Repository conventions

Keep public documentation current as architecture changes.

Recommended top-level structure:

```text
README.md
ROADMAP.md
SECURITY.md
PRIVACY.md
CONTRIBUTING.md
docs/
src/
tests/
.github/
```

The exact source layout may evolve, but architecture boundaries should remain explicit.

## Local development

The project must provide a reproducible setup from a clean checkout.

At minimum, implementation should eventually provide commands for:

```text
install dependencies
run tests
run lint/type checks
run formatting checks
run the application locally
run source fixtures
```

Do not document commands until they actually exist in the repository.

## Testing strategy

### Unit tests

Test parsers, normalizers, state transitions, hashing, deduplication and notification decisions independently.

### Fixture tests

Store representative official HTML/PDF-derived fixtures so parser behavior can be tested without repeatedly hitting VGU.

### Integration tests

Exercise the pipeline from acquisition fixture through evidence, extraction, verification and delivery decision.

### Regression tests

Every discovered production bug should become a regression fixture/test where practical.

### Safety tests

Explicitly test that:

- unverified community information is not published as official;
- missing sources do not erase last-known-good data;
- duplicate runs do not duplicate notifications;
- conflicting official evidence remains conflicting;
- AI output cannot create authoritative claims without evidence.

## Source testing

Live-source tests should be separated from deterministic fixture tests.

A temporary VGU outage must not make the entire test suite meaningless.

## Secrets

Never commit:

- Telegram bot tokens;
- Cloudflare credentials;
- API keys;
- cookies;
- personal student data;
- ERP credentials.

Use environment variables or the repository's secret-management mechanism in deployment.

## Data handling during development

Prefer synthetic users and local fixtures. Do not copy real student information into fixtures unless there is an explicit, documented legal and privacy reason.

## Pull requests

A change should explain:

1. what changed;
2. why it changed;
3. what trust boundary it affects;
4. what tests were added/updated;
5. whether source behavior changed;
6. whether documentation needs updating.

## Dependency policy

Every dependency should justify its cost in complexity, maintenance and runtime resources.

Free/open-source dependencies are preferred, but “free” does not mean automatically suitable. Security, maintenance and deterministic behavior still matter.

## AI development policy

AI coding assistants may be used to accelerate development, but generated code must satisfy the same tests and review standards as hand-written code.

AI must not be used as a substitute for source verification.
