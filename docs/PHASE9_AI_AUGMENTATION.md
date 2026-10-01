# Phase 9 — AI Augmentation

## Goal
Add optional AI assistance without changing the VGU Signal authority model. **No local LLM is required.** The AI layer is a remote, provider-agnostic HTTP adapter.

## Provider
Optional Worker variables:
- AI_API_KEY — secret; absent means AI is disabled.
- AI_API_BASE — optional provider-compatible base; defaults to Gemini Developer API.
- AI_MODEL — defaults to gemini-2.5-flash-lite.
- AI_EMBEDDING_MODEL — defaults to gemini-embedding-2.

If the key is absent, quota is exhausted, or the provider fails, deterministic Phase 8 features remain usable.

## Trust boundary
official source → evidence → verified claim → InformationItem → deterministic retrieval → AI interpretation → answer + official source links.

AI never verifies claims, changes claim state, creates authoritative InformationItems, or invents deadlines/dates.

## Roadmap coverage
- Source-grounded summaries: grounded responses require citations to supplied VERIFIED InformationItems.
- Difficult document explanation: the same grounded path explains complicated notices/calendars/exam/fee records.
- Semantic retrieval: remote embeddings plus deterministic cosine similarity; vectors are cacheable in D1.
- Natural-language queries: Phase 9 /ask path will use AI-assisted retrieval then grounded generation.
- Community submission matching: AI may assist ranking/interpretation only after deterministic official candidates exist; Phase 7 remains authoritative.
- AI evaluation suite: structured output, citation and similarity tests.
- Hallucination/grounding tests: invalid/citation-free answers are rejected.

## Zero-cost operation
No paid provider is required and there is no automatic paid fallback. Provider quotas can change, so production deployment must re-check the current free limits. Google currently documents a free Gemini API tier with selected free models and lists gemini-2.5-flash-lite as free for standard input/output.

## Exit gate
The Phase 9 implementation must keep AI optional and preserve deterministic fallback whenever the remote provider is unavailable.
