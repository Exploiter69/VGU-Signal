# Contributing to VGU Signal

Thank you for helping improve VGU Signal.

## Before contributing

Read:

- [Architecture](docs/ARCHITECTURE.md)
- [Trust Model](docs/TRUST_MODEL.md)
- [Source Strategy](docs/SOURCE_STRATEGY.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Security Policy](SECURITY.md)

## Most important rule

**Do not weaken the evidence chain.**

A feature that makes information look more convenient while making its origin or correctness less clear is not an acceptable improvement.

## Source contributions

When adding a VGU source:

- identify the official URL;
- explain why it is authoritative or useful;
- document acquisition behavior;
- respect public-access boundaries and site policies;
- add fixtures where practical;
- test failure and change behavior.

Do not add authenticated scraping that depends on student credentials.

## Code contributions

Prefer small, composable components with explicit inputs and outputs.

Business logic should not be hidden inside:

- Telegram handlers;
- scrapers;
- AI prompts;
- deployment scripts.

## Community information

Do not treat a community submission as authoritative. Any code handling community signals must preserve the distinction between discovery and verification.

## Pull requests

Include:

- problem statement;
- implementation summary;
- tests;
- trust implications;
- documentation changes.

## Security

Do not open a public issue for a suspected security vulnerability. Follow [SECURITY.md](SECURITY.md).
