# Project Status

**As of 2026-10-01**

## Current stage

**Phase 5 — Telegram MVP: COMPLETE.**

Phase 0 through Phase 4 remain closed. Phase 5 adds the first student-facing delivery channel while preserving verification and information-model boundaries.

## Phase 5 implementation

The Telegram MVP provides:

- Telegram Bot API webhook foundation;
- durable /start onboarding for program, branch, year, semester and categories;
- /latest;
- /upcoming;
- /search;
- conservative /verify;
- /settings;
- source/provenance display;
- deadline reminders;
- weekly digest;
- notification deduplication;
- quiet hours and mute controls;
- D1-backed user, preference, session and notification state.

Migration 0005_telegram_mvp.sql contains the delivery state schema.

## Phase 5 trust boundary

Only current verified information is delivered by student-facing query paths. Telegram rendering does not make verification decisions. /verify reports matching official evidence and says "Not officially confirmed" when no current match exists; it does not call unmatched information false.

## Phase 5 exit gate

**COMPLETE.** A student can subscribe through /start, configure relevance preferences, receive filtered verified information, inspect the official source, and see when an item is changed, superseding or correcting earlier information. Reminder/digest delivery has durable deduplication and respects notification controls.

## Quality gate

~~~text
ruff format --check .
ruff check .
mypy src
pytest -q
worker: npm install && npm run typecheck
~~~

## Next gate

**Phase 6 — Production-free infrastructure.**
