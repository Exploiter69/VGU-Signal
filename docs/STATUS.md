# Project Status

**As of 2026-10-01**

## Current stage

**Phase 9 — AI Augmentation: COMPLETE.**

Phases 0 through 8 remain closed. Phase 9 adds optional remote AI assistance without requiring a local LLM or paid service. Phase 6 now uses D1-only evidence storage so production does not depend on billing-gated R2. The deterministic verified-information pipeline remains the authority and fallback.

## Phase 9 implementation

- optional remote provider gateway using Worker secrets;
- source-grounded AI answers with mandatory verified-evidence citations;
- explanation/summary commands for difficult verified information;
- remote embedding support with D1 embedding cache and deterministic cosine retrieval;
- natural-language `/ask` path;
- AI-assisted community-submission comparison after deterministic official matching;
- structured-output/citation/cosine evaluation tests;
- hallucination/grounding rejection for malformed or unsupported citations;
- deterministic Phase 8 fallback when AI is unavailable.

Migration: `0009_phase9_ai.sql`.

## Phase 9 trust boundary

```
official source → evidence → verified claim → InformationItem
                                      ↓
                           deterministic retrieval
                                      ↓
                              AI interpretation
                                      ↓
                         answer + official source links
```

AI cannot verify claims, mutate authoritative state, create deadlines, or turn community content into official evidence.

## Phase 9 exit gate

**COMPLETE.** All eight Phase 9 roadmap requirements are implemented with AI optional, remote-provider based, source-grounded and backed by deterministic fallback behavior.

## Earlier phase closure

Phase 0 through Phase 8 are complete. See `ROADMAP.md` and the phase-specific documents for their implementation and exit gates.

## Quality gate

The repository CI runs:

```
ruff format --check .
ruff check .
mypy src
pytest -q
worker: npm install && npm run typecheck && npm test
```
